from pyparsejson.rules.base import Rule
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

class WrapLoosePairsRule(Rule):
    """
    Envuelve el contenido en {} si parece ser un objeto suelto (pares clave-valor)
    y no empieza ya con { o [.
    """
    name = "WrapLoosePairs"
    priority = 5

    def applies(self, context: Context) -> bool:
        if not context.tokens:
            return False
        first = context.tokens[0]
        # Si no empieza con { o [, asumimos que necesita envoltura si hay colons o assigns
        if first.type not in (TokenType.LBRACE, TokenType.LBRACKET):
            # Verificar si hay estructura de pares
            has_pairs = any(t.type in (TokenType.COLON, TokenType.ASSIGN) for t in context.tokens)
            return has_pairs
        return False

    def apply(self, context: Context):
        # Insertar { al inicio y } al final
        # Ajustar posiciones es irrelevante para la lógica, pero mantenemos consistencia
        
        l_brace = Token(TokenType.LBRACE, "{", "{", 0)
        r_brace = Token(TokenType.RBRACE, "}", "}", 0) # Posición dummy
        
        context.tokens.insert(0, l_brace)
        context.tokens.append(r_brace)
        context.record_rule(self.name)
