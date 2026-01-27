import re

from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry

DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


@RuleRegistry.register(tags=["values", "dates"], priority=45)
class DateLiteralToStringRule(Rule):

    def applies(self, context: Context) -> bool:
        return any(
            t.type == TokenType.NUMBER and DATE_PATTERN.fullmatch(t.value)
            for t in context.tokens
        )

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
            if token.type == TokenType.NUMBER and DATE_PATTERN.fullmatch(token.value):
                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)
