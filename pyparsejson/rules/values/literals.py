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
    """Une strings consecutivos en un solo valor"""

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i in range(len(tokens) - 1):
            if (tokens[i].type == TokenType.STRING and
                    tokens[i + 1].type == TokenType.STRING):
                return True
        return False

    def apply(self, context: Context):
        new_tokens = []
        i = 0

        while i < len(context.tokens):
            current = context.tokens[i]

            # Si es STRING y el siguiente también
            if (i + 1 < len(context.tokens) and
                    current.type == TokenType.STRING and
                    context.tokens[i + 1].type == TokenType.STRING):

                # Unir todos los strings consecutivos
                merged_value = current.value.strip('"')
                i += 1

                while (i < len(context.tokens) and
                       context.tokens[i].type == TokenType.STRING):
                    merged_value += " " + context.tokens[i].value.strip('"')
                    i += 1

                # Crear token unificado
                new_tokens.append(Token(
                    type=TokenType.STRING,
                    value=f'"{merged_value}"',
                    raw_value=f'"{merged_value}"',
                    position=current.position
                ))
            else:
                new_tokens.append(current)
                i += 1

        context.tokens = new_tokens
        context.mark_changed()
        context.record_rule(self.name)