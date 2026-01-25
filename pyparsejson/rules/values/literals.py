from pyparsejson.rules.base import Rule
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

class NormalizeBooleansRule(Rule):
    """
    Normaliza booleanos humanos (si, no, yes, on, off) a true/false.
    """
    name = "NormalizeBooleans"
    priority = 50

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

class QuoteBareWordsRule(Rule):
    """
    Convierte palabras sueltas (BARE_WORD) en strings si parecen ser claves o valores de texto.
    """
    name = "QuoteBareWords"
    priority = 60

    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BARE_WORD for t in context.tokens)

    def apply(self, context: Context):
        for token in context.tokens:
            if token.type == TokenType.BARE_WORD:
                # Convertir a STRING
                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                context.record_rule(self.name)
