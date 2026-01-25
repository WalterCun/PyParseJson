from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

@RuleRegistry.register(tags=["structure", "pre_repair"], priority=5)
class WrapLoosePairsRule(Rule):
    """
    Envuelve el contenido en {} si parece ser un objeto suelto (pares clave-valor)
    y no empieza ya con { o [.
    """
    def applies(self, context: Context) -> bool:
        if not context.tokens:
            return False
        first = context.tokens[0]
        if first.type not in (TokenType.LBRACE, TokenType.LBRACKET):
            has_pairs = any(t.type in (TokenType.COLON, TokenType.ASSIGN) for t in context.tokens)
            return has_pairs
        return False

    def apply(self, context: Context):
        l_brace = Token(TokenType.LBRACE, "{", "{", 0)
        r_brace = Token(TokenType.RBRACE, "}", "}", 0)
        
        context.tokens.insert(0, l_brace)
        context.tokens.append(r_brace)
        context.record_rule(self.name)
