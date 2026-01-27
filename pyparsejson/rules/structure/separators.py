from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=10)
class EqualToColonRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.ASSIGN for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
            if token.type == TokenType.ASSIGN:
                token.type = TokenType.COLON
                token.value = ":"  # <--- CORREGIDO (faltaba comilla de cierre)
                token.raw_value = ":"  # <--- CORREGIDO (faltaba comilla de cierre)
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=20)
class AddMissingCommasRule(Rule):
    def applies(self, context: Context) -> bool:
        return len(context.tokens) > 1

    def apply(self, context: Context):
        new_tokens = []
        i = 0
        changed = False

        while i < len(context.tokens):
            current_token = context.tokens[i]
            new_tokens.append(current_token)

            if i + 1 < len(context.tokens):
                next_token = context.tokens[i + 1]

                # --- MODIFICACIÓN AQUÍ ---
                is_current_value_end = current_token.type in (
                    TokenType.STRING,
                    TokenType.NUMBER,
                    TokenType.BOOLEAN,
                    TokenType.NULL,
                    TokenType.RBRACE,
                    TokenType.RBRACKET,
                    TokenType.BARE_WORD  # <--- AÑADIDO
                )
                is_next_potential_key = next_token.type in (TokenType.STRING, TokenType.BARE_WORD)

                if is_current_value_end and is_next_potential_key:
                    if i + 2 < len(context.tokens) and context.tokens[i + 2].type == TokenType.COLON:
                        comma_token = Token(TokenType.COMMA, ",", ",", current_token.position + 1)
                        new_tokens.append(comma_token)
                        changed = True
            i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "values"], priority=15)
class TupleToListRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type in (TokenType.LPAREN, TokenType.RPAREN) for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
            if token.type == TokenType.LPAREN:
                token.type = TokenType.LBRACKET
                token.value = "["  # <--- CORREGIDO
                token.raw_value = "["  # <--- CORREGIDO
                changed = True
            elif token.type == TokenType.RPAREN:
                token.type = TokenType.RBRACKET
                token.value = "]"  # <--- CORREGIDO
                token.raw_value = "]"  # <--- CORREGIDO
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)