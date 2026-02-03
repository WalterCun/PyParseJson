from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType
from pyparsejson.core import token as core_token
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


@RuleRegistry.register(tags=["values", "normalization"], priority=50)
class NormalizeBooleansRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BOOLEAN for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        true_vals = {'1', 1, 'si', 'yes', 'on', 'true'}
        false_vals = {'0', 0, 'no', 'off', 'false'}

        for token in context.tokens:
            if token.type == TokenType.BOOLEAN:
                lower_val = token.value.lower()

                if lower_val in true_vals and token.value != 'true':
                    token.value = 'true'
                    token.raw_value = 'true'
                    changed = True
                elif lower_val in false_vals and token.value != 'false':
                    token.value = 'false'
                    token.raw_value = 'false'
                    changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["values", "normalization"], priority=20)
class MergeFreeTextValueRule(Rule):
    """
    Une tokens consecutivos en un único valor de tipo string después de un separador (: o =),
    para manejar texto libre que el tokenizador podría haber separado.
    Se detiene ante una coma, cierre de estructura (}, ]) o el inicio de una nueva clave.

    Ejemplo: `user: admin // superuser` se convierte en `"user": "admin // superuser"`
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i in range(len(tokens) - 2):
            if tokens[i].type in (TokenType.COLON, TokenType.ASSIGN):
                # Potencial inicio de un valor multi-token.
                val_token1 = tokens[i + 1]
                val_token2 = tokens[i + 2]

                # No aplicar si el valor es una estructura JSON.
                if val_token1.type in (TokenType.LBRACE, TokenType.LBRACKET):
                    continue

                # Si el siguiente token ya es un delimitador, no hay nada que unir.
                if val_token2.type in (TokenType.COMMA, TokenType.RBRACE, TokenType.RBRACKET):
                    continue

                # Comprobar si `val_token2` es el inicio de una nueva clave.
                # Patrón: `: valor1 clave2 :`
                if i + 3 < len(tokens) and tokens[i + 3].type in (TokenType.COLON, TokenType.ASSIGN):
                    if val_token2.type in (TokenType.BARE_WORD, TokenType.STRING):
                        continue

                # Si llegamos aquí, tenemos un patrón como `: token1 token2 ...` que no es una nueva clave.
                # Esto indica que los tokens deben unirse.
                return True
        return False

    def apply(self, context: Context):
        new_tokens = []
        i = 0
        changed = False

        while i < len(context.tokens):
            token = context.tokens[i]

            if token.type in (TokenType.COLON, TokenType.ASSIGN) and i + 1 < len(context.tokens):
                new_tokens.append(token)  # Conservar el separador

                val_start_idx = i + 1
                val_end_idx = -1

                # Buscar el final del valor.
                for j in range(val_start_idx, len(context.tokens)):
                    current_val_token = context.tokens[j]

                    # El valor termina con un delimitador.
                    if current_val_token.type in (TokenType.COMMA, TokenType.RBRACE, TokenType.RBRACKET):
                        val_end_idx = j - 1
                        break

                    # Verificaciones de lookahead para detectar nuevas claves
                    if j + 1 < len(context.tokens):
                        next_token = context.tokens[j + 1]
                        
                        # 2. Detectar inicio de clave simple: NEXT + COLON
                        # Ejemplo: ... valor clave : ...
                        if next_token.type in (TokenType.BARE_WORD, TokenType.STRING) and \
                           j + 2 < len(context.tokens) and \
                           context.tokens[j + 2].type in (TokenType.COLON, TokenType.ASSIGN):
                            val_end_idx = j
                            break
                    
                    # Si no hay delimitador, el valor se extiende hasta el final.
                    val_end_idx = j

                if val_end_idx < val_start_idx:
                    i += 1
                    continue

                tokens_to_merge = context.tokens[val_start_idx : val_end_idx + 1]

                # Regla del usuario: NO aplicar si el valor es NUMBER, BOOLEAN, NULL ni estructura.
                # Si es un solo token y es de tipo preservable, no fusionar (dejarlo como está)
                if len(tokens_to_merge) == 1:
                    single = tokens_to_merge[0]
                    if single.type in (TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL):
                        new_tokens.append(single)
                        i = val_end_idx + 1
                        continue

                # Solo unir si no contienen estructuras.
                can_merge = len(tokens_to_merge) > 0 and \
                            all(t.type not in (TokenType.LBRACE, TokenType.RBRACE, TokenType.LBRACKET, TokenType.RBRACKET, TokenType.COLON, TokenType.ASSIGN) for t in tokens_to_merge)

                if can_merge:
                    first_token = tokens_to_merge[0]
                    last_token = tokens_to_merge[-1]
                    
                    # Extraer el texto original para preservar espacios y caracteres especiales.
                    start_pos = first_token.position
                    end_pos = last_token.position + len(last_token.raw_value)
                    # CORRECCIÓN: Usar initial_text en lugar de text.
                    merged_value_str = context.initial_text[start_pos:end_pos].strip()

                    # Crear un único token de tipo STRING. El finalizador se encargará de las comillas.
                    new_token = core_token.Token(
                        type=TokenType.STRING,
                        value=merged_value_str,
                        raw_value=merged_value_str,
                        position=first_token.position,
                        line=first_token.line,
                        column=first_token.column
                    )
                    new_tokens.append(new_token)
                    
                    i = val_end_idx + 1
                    changed = True
                else:
                    # No se pudo unir, copiar los tokens tal cual.
                    new_tokens.extend(tokens_to_merge)
                    i = val_end_idx + 1
            else:
                new_tokens.append(token)
                i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["values", "normalization"], priority=60)
class QuoteBareWordsRule(Rule):
    """
    Convierte BARE_WORD en strings JSON válidos SOLO para valores (no claves).
    Las claves ya deben haber sido procesadas por QuoteKeysRule (priority 30).
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i, token in enumerate(tokens):
            if token.type == TokenType.BARE_WORD:
                # Es clave si el siguiente token es : o =
                if i + 1 < len(tokens) and tokens[i + 1].type in (TokenType.COLON, TokenType.ASSIGN):
                    continue  # Saltar claves - ya procesadas por QuoteKeysRule
                return True
        return False

    def apply(self, context: Context):
        changed = False
        for i, token in enumerate(context.tokens):
            if token.type == TokenType.BARE_WORD:
                # Saltar claves (ya procesadas por QuoteKeysRule)
                if i + 1 < len(context.tokens) and context.tokens[i + 1].type in (TokenType.COLON, TokenType.ASSIGN):
                    continue

                # Convertir valor a string con comillas dobles SIMPLES
                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["values", "normalization"], priority=65)
class MergeAdjacentStringsRule(Rule):
    """
    Une strings consecutivos en un solo valor.

    VERSIÓN CORREGIDA: No une strings que son claves (seguidas de :)
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i in range(len(tokens) - 1):
            current = tokens[i]
            next_token = tokens[i + 1]

            # Detectar strings consecutivos
            if current.type == TokenType.STRING and next_token.type == TokenType.STRING:
                # ⚠️ VERIFICACIÓN CRÍTICA: Patrón : string1 string2 :
                # Este es el caso: user: "admin" "active" :
                # NO unir solo si AMBOS están entre COLON
                if i > 0 and i + 2 < len(tokens):
                    prev_token = tokens[i - 1]
                    next_next = tokens[i + 2]

                    # Patrón : valor clave :
                    if prev_token.type == TokenType.COLON and next_next.type == TokenType.COLON:
                        continue  # NO UNIR

                return True

        return False

    def apply(self, context: Context):
        new_tokens = []
        i = 0

        while i < len(context.tokens):
            current = context.tokens[i]

            # Verificar si es STRING seguido de otro STRING
            if (i + 1 < len(context.tokens) and
                    current.type == TokenType.STRING and
                    context.tokens[i + 1].type == TokenType.STRING):

                # ⚠️ ÚNICA PROTECCIÓN: Patrón : string1 string2 : → NO UNIR
                if i > 0 and i + 2 < len(context.tokens):
                    prev_token = context.tokens[i - 1]
                    next_next = context.tokens[i + 2]

                    if prev_token.type == TokenType.COLON and next_next.type == TokenType.COLON:
                        # Detectado: user: "admin" "active" :
                        # NO unir "admin" + "active"
                        new_tokens.append(current)
                        i += 1
                        continue

                # ✅ SEGURO UNIR: Acumular todos los strings consecutivos
                merged_value = current.value.strip('"')
                i += 1

                while i < len(context.tokens):
                    next_token = context.tokens[i]

                    # ¿El siguiente es string?
                    if next_token.type != TokenType.STRING:
                        break

                    # ⚠️ Protección de patrón durante acumulación
                    # Si estamos a punto de añadir un string que está seguido de :
                    # Y el string actual (merged) vino después de :
                    # NO añadir ese string
                    if (i + 1 < len(context.tokens) and
                            context.tokens[i + 1].type == TokenType.COLON and
                            i - 1 >= 0):
                        # Verificar si merged_value comenzó después de :
                        # (esto solo importa si hay : antes del primer string)
                        break

                    # Unir
                    merged_value += " " + next_token.value.strip('"')
                    i += 1

                # Crear token unificado
                new_tokens.append(core_token.Token(
                    type=TokenType.STRING,
                    value=f'"{merged_value}"',
                    raw_value=f'"{merged_value}"',
                    position=current.position,
                    line=current.line,
                    column=current.column
                ))
            else:
                new_tokens.append(current)
                i += 1

        if len(new_tokens) != len(context.tokens):
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)
