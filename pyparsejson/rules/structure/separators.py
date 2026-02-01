# Path: pyparsejson\rules\structure\separators.py
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=10)
class EqualToColonRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.ASSIGN for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
            if token.type == TokenType.ASSIGN:
                token.type = TokenType.COLON
                token.value = ":"
                token.raw_value = ":"
                changed = True
        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=20)
class AddMissingCommasRule(Rule):
    """
    Inserta comas faltantes entre pares clave:valor.

    VERSIÓN MEJORADA: Soporta claves compuestas por múltiples tokens (multi-word keys).
    Escanea hacia adelante para encontrar el separador definitivo (: o =).
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        for i in range(len(tokens) - 1):
            current = tokens[i]

            # 1. Verificar si el token actual es el FIN de un valor
            is_value_end = current.type in (
                TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN,
                TokenType.NULL, TokenType.RBRACE, TokenType.RBRACKET, TokenType.RPAREN
            )

            if not is_value_end:
                continue

            # 2. Buscar el siguiente separador (COLON o ASSIGN) para determinar dónde termina la próxima clave
            #    Buscamos en el rango i+1 hasta len(tokens)
            next_sep_idx = -1
            j = i + 1
            while j < len(tokens):
                if tokens[j].type in (TokenType.COLON, TokenType.ASSIGN):
                    next_sep_idx = j
                    break
                j += 1

            # Si no encontramos separador, no hay par clave:valor siguiente
            if next_sep_idx == -1:
                continue

            # 3. Verificar si hay un token inmediatamente después del valor actual que pueda ser clave
            if i + 1 >= next_sep_idx:
                continue  # No hay espacio para una clave

            # 4. El candidato a clave es el token en i+1
            next_token = tokens[i + 1]

            # Si el candidato ya es una COMMA, todo está bien
            if next_token.type == TokenType.COMMA:
                continue

            # Si el candidato es parte de una clave (BARE_WORD o STRING) y eventualmente le sigue un separador,
            # entonces necesitamos insertar una coma antes de él.
            is_potential_key = next_token.type in (TokenType.BARE_WORD, TokenType.STRING)

            if is_potential_key:
                # Verificamos que entre i+1 y next_sep_idx solo haya elementos válidos de clave (palabras o strings)
                valid_key_parts = True
                for k in range(i + 1, next_sep_idx):
                    if tokens[k].type not in (TokenType.BARE_WORD, TokenType.STRING):
                        valid_key_parts = False
                        break

                if valid_key_parts:
                    return True

        return False

    def apply(self, context: Context):
        tokens = context.tokens
        new_tokens = []
        i = 0
        changed = False

        while i < len(tokens):
            current = tokens[i]
            new_tokens.append(current)

            # Necesitamos espacio para buscar
            if i + 1 >= len(tokens):
                i += 1
                continue

            # Lógica similar a applies(): buscar el separador final para definir la clave
            is_value_end = current.type in (
                TokenType.STRING,
                TokenType.NUMBER,
                TokenType.BOOLEAN,
                TokenType.NULL,
                TokenType.RBRACE,
                TokenType.RBRACKET
            )

            if not is_value_end:
                i += 1
                continue

            # Buscar índice del siguiente separador
            next_sep_idx = -1
            j = i + 1
            while j < len(tokens):
                if tokens[j].type in (TokenType.COLON, TokenType.ASSIGN):
                    next_sep_idx = j
                    break
                j += 1

            # Si no hay estructura clave:valor siguiente, continuar
            if next_sep_idx == -1:
                i += 1
                continue

            # Revisar el token inmediatamente siguiente
            next_token_candidate = tokens[i + 1]

            # Si ya hay coma, o el siguiente no parece un inicio de clave, continuar
            if next_token_candidate.type == TokenType.COMMA:
                i += 1
                continue

            if next_token_candidate.type not in (TokenType.BARE_WORD, TokenType.STRING):
                i += 1
                continue

            # Validar que los tokens entre aquí y el separador sean válidos para una clave
            valid_key_sequence = True
            for k in range(i + 1, next_sep_idx):
                if tokens[k].type not in (TokenType.BARE_WORD, TokenType.STRING):
                    valid_key_sequence = False
                    break

            if valid_key_sequence:
                # INSERTAR COMMA
                comma = Token(
                    type=TokenType.COMMA,
                    value=",",
                    raw_value=",",
                    position=current.position + len(current.value),
                    line=current.line,
                    column=current.column + len(current.value)
                )
                new_tokens.append(comma)
                changed = True

            i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "values"], priority=20)
class TupleToListRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type in (TokenType.LPAREN, TokenType.RPAREN) for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
            if token.type == TokenType.LPAREN:
                token.type = TokenType.LBRACKET
                token.value = "["
                token.raw_value = "["
                changed = True
            elif token.type == TokenType.RPAREN:
                token.type = TokenType.RBRACKET
                token.value = "]"
                token.raw_value = "]"
                changed = True
        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "normalization"], priority=30)
class QuoteKeysRule(Rule):
    """Envuelve TODAS las claves en comillas dobles"""

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i in range(len(tokens) - 1):
            token = tokens[i]
            next_token = tokens[i + 1]

            # Es clave si está seguida de : o =
            is_key = token.type in (TokenType.BARE_WORD, TokenType.STRING)
            is_separator = next_token.type == TokenType.COLON

            if is_key and is_separator:
                # Verificar si ya tiene comillas dobles correctas
                if token.type == TokenType.STRING:
                    if token.value.startswith('"') and token.value.endswith('"'):
                        continue  # Ya está correcta
                return True
        return False

    def apply(self, context: Context):
        new_tokens = []
        changed = False

        for i, token in enumerate(context.tokens):
            # Mirar hacia adelante para ver si es clave
            # Nota: QuoteKeysRule debe ejecutarse después de AddMissingCommasRule
            is_key = (
                    i + 1 < len(context.tokens) and
                    context.tokens[i + 1].type == TokenType.COLON and
                    token.type in (TokenType.BARE_WORD, TokenType.STRING)
            )

            if is_key:
                # Limpiar valor (quitar comillas simples o existentes)
                clean_val = token.value.strip('"\'')

                # Crear nuevo token con comillas dobles
                new_token = Token(
                    type=TokenType.STRING,
                    value=f'"{clean_val}"',
                    raw_value=f'"{clean_val}"',
                    position=token.position,
                    line=token.line,
                    column=token.column
                )
                new_tokens.append(new_token)
                changed = True
            else:
                new_tokens.append(token)

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "cleanup"], priority=99)
class BalanceBracketsRule(Rule):
    """
    Asegura balance final de llaves y corchetes.

    VERSIÓN CORREGIDA: Se ejecuta cuando detecta desbalance, no solo en última iteración.
    """

    def applies(self, context: Context) -> bool:
        """Detecta si hay desbalance de llaves o corchetes"""
        tokens = context.tokens
        if not tokens:
            return False

        stack = []
        errors = 0

        for token in tokens:
            if token.type in (TokenType.LBRACE, TokenType.LBRACKET):
                stack.append(token.type)
            elif token.type in (TokenType.RBRACE, TokenType.RBRACKET):
                if not stack:
                    errors += 1  # Cierre sin apertura
                else:
                    last = stack.pop()
                    # Verificar que coincidan (no mezclar { con ])
                    if (token.type == TokenType.RBRACE and last != TokenType.LBRACE) or \
                            (token.type == TokenType.RBRACKET and last != TokenType.LBRACKET):
                        errors += 1  # Tipo incorrecto

        # Si quedaron elementos en stack, hay llaves/corchetes sin cerrar
        # O si hubo errores de tipo
        return len(stack) > 0 or errors > 0

    def apply(self, context: Context):
        """Añade cierres faltantes al final del documento"""
        tokens = context.tokens
        stack = []

        # Detectar qué cierres faltan
        for token in tokens:
            if token.type == TokenType.LBRACE:
                stack.append(TokenType.RBRACE)
            elif token.type == TokenType.LBRACKET:
                stack.append(TokenType.RBRACKET)
            elif token.type in (TokenType.RBRACE, TokenType.RBRACKET):
                # Solo hacer pop si coincide el tipo
                if stack and stack[-1] == token.type:
                    stack.pop()

        # Añadir cierres faltantes en orden LIFO
        if stack:
            for close_type in reversed(stack):
                char = "}" if close_type == TokenType.RBRACE else "]"
                context.tokens.append(Token(
                    type=close_type,
                    value=char,
                    raw_value=char,
                    position=len(context.tokens),
                    line=0,
                    column=0
                ))

            context.mark_changed()
            context.record_rule(self.name)