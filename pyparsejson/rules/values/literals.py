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
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.BARE_WORD for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for i, token in enumerate(context.tokens):
            if token.type == TokenType.BARE_WORD:
                is_key = False
                if i + 1 < len(context.tokens):
                    if context.tokens[i + 1].type == TokenType.COLON:
                        is_key = True

                if is_key:
                    continue  # ⬅️ NO TOCAR CLAVES

                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)
