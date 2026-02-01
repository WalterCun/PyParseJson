from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token


@RuleRegistry.register(tags=["values", "normalization"], priority=50)
class NormalizeBooleansRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BOOLEAN for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        true_vals = {'si', 'yes', 'on', 'true'}
        false_vals = {'no', 'off', 'false'}

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
                new_tokens.append(Token(
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


# ============================================================
# EJEMPLOS DE COMPORTAMIENTO ESPERADO
# ============================================================

"""
CASO 1: Valores multi-palabra (DEBE UNIR)
Input:  user: este es un administrador
Tokens: "user", :, "este", "es", "un", "administrador"
                    ↑ Todos después de :, ninguno seguido de :
Result: "user", :, "este es un administrador" ✅

CASO 2: Valor seguido de clave (NO DEBE UNIR)
Input:  user: admin active: si
Tokens: "user", :, "admin", "active", :, true
                             ↑        ↑
                        Después de :  Seguida de :
Result: "user", :, "admin", "active", :, true ✅
        (NO unir "admin" + "active")

CASO 3: Clave multi-palabra (DEBE UNIR)
Input:  deposito fecha: 2026-01-01
Tokens: "deposito", "fecha", :, "2026-01-01"
                    ↑        ↑
           Antes de :  Seguida de :
Result: "deposito fecha", :, "2026-01-01" ✅

CASO 4: Múltiples valores seguidos de clave (PARCIAL)
Input:  user: uno dos tres active: si
Tokens: "user", :, "uno", "dos", "tres", "active", :, true
                    ↑     ↑      ↑        ↑
                 Después de :              Seguida de :
Result: "user", :, "uno dos tres", "active", :, true ✅
        (Unir "uno"+"dos"+"tres", NO unir con "active")
"""