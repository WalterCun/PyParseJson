from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

@RuleRegistry.register(tags=["values", "normalization"], priority=50)
class NormalizeBooleansRule(Rule):
    """
    Normaliza booleanos humanos (si, no, yes, on, off) a true/false.
    """
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BOOLEAN for t in context.tokens)

    def apply(self, context: Context):
        true_vals = ['si', 'yes', 'on', 'true']
        false_vals = ['no', 'off', 'false']
        
        for token in context.tokens:
            if token.type == TokenType.BOOLEAN:
                lower_val = token.value.lower()
                if lower_val in true_vals and token.value != 'true':
                    token.value = 'true'
                    token.raw_value = 'true'
                    context.record_rule(self.name)
                elif lower_val in false_vals and token.value != 'false':
                    token.value = 'false'
                    token.raw_value = 'false'
                    context.record_rule(self.name)

@RuleRegistry.register(tags=["values", "normalization"], priority=60)
class QuoteBareWordsRule(Rule):
    """
    Convierte palabras sueltas (BARE_WORD) en strings si parecen ser claves o valores de texto.
    """
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BARE_WORD for t in context.tokens)

    def apply(self, context: Context):
        for token in context.tokens:
            if token.type == TokenType.BARE_WORD:
                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                context.record_rule(self.name)
