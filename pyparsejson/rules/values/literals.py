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
        true_vals = ['si', 'yes', 'on', 'true']
        false_vals = ['no', 'off', 'false']

        for token in context.tokens:
            if token.type == TokenType.BOOLEAN:
                lower_val = token.value.lower()
                # --- CORRECCIÓN DE SINTAXIS ---
                # Se agrupan listas y se usa 'and' para dar prioridad a la comprobación de la primera.
                if lower_val in (true_vals + false_vals):
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
    Convierte palabras clave sin comillas en strings JSON válidos.
    user: -> "user":
    """

    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BARE_WORD for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for i, token in enumerate(context.tokens):
            if token.type == TokenType.BARE_WORD:
                # Convertir TODAS las palabras sin comillas a strings (claves y valores)
                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)