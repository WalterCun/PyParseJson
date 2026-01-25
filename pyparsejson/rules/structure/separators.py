from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

@RuleRegistry.register(tags=["structure", "pre_repair"], priority=10)
class EqualToColonRule(Rule):
    """
    Convierte asignaciones con '=' a ':' cuando parece ser un par clave-valor.
    Ej: key=value -> key:value
    """
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.ASSIGN for t in context.tokens)

    def apply(self, context: Context):
        for token in context.tokens:
            if token.type == TokenType.ASSIGN:
                token.type = TokenType.COLON
                token.value = ":"
                token.raw_value = ":"
                context.record_rule(self.name)

@RuleRegistry.register(tags=["structure", "pre_repair"], priority=20)
class AddMissingCommasRule(Rule):
    """
    Inserta comas faltantes entre elementos de objetos o listas.
    Ej: "a":1 "b":2 -> "a":1, "b":2
    """
    def applies(self, context: Context) -> bool:
        return True 

    def apply(self, context: Context):
        new_tokens = []
        value_enders = [TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.RBRACE, TokenType.RBRACKET, TokenType.BARE_WORD]
        value_starters = [TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.LBRACE, TokenType.LBRACKET, TokenType.BARE_WORD]
        
        for i, token in enumerate(context.tokens):
            new_tokens.append(token)
            
            if i + 1 < len(context.tokens):
                next_token = context.tokens[i+1]
                
                if token.type in value_enders and next_token.type in value_starters:
                    is_next_a_key = False
                    if i + 2 < len(context.tokens):
                        if context.tokens[i+2].type == TokenType.COLON:
                            is_next_a_key = True
                    
                    if is_next_a_key:
                        new_tokens.append(Token(TokenType.COMMA, ",", ",", token.position + len(token.raw_value)))
                        context.record_rule(self.name)

        if len(new_tokens) > len(context.tokens):
            context.tokens = new_tokens

@RuleRegistry.register(tags=["structure", "values"], priority=15)
class TupleToListRule(Rule):
    """
    Convierte tuplas (..) en listas [..].
    """
    def applies(self, context: Context) -> bool:
        return any(t.type in (TokenType.LPAREN, TokenType.RPAREN) for t in context.tokens)

    def apply(self, context: Context):
        for token in context.tokens:
            if token.type == TokenType.LPAREN:
                token.type = TokenType.LBRACKET
                token.value = "["
                token.raw_value = "["
                context.record_rule(self.name)
            elif token.type == TokenType.RPAREN:
                token.type = TokenType.RBRACKET
                token.value = "]"
                token.raw_value = "]"
                context.record_rule(self.name)
