from pyparsejson.rules.base import Rule
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

class EqualToColonRule(Rule):
    """
    Convierte asignaciones con '=' a ':' cuando parece ser un par clave-valor.
    Ej: key=value -> key:value
    """
    name = "EqualToColon"
    priority = 10

    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.ASSIGN for t in context.tokens)

    def apply(self, context: Context):
        for token in context.tokens:
            if token.type == TokenType.ASSIGN:
                token.type = TokenType.COLON
                token.value = ":"
                token.raw_value = ":"
                context.record_rule(self.name)

class AddMissingCommasRule(Rule):
    """
    Inserta comas faltantes entre elementos de objetos o listas.
    Ej: "a":1 "b":2 -> "a":1, "b":2
    """
    name = "AddMissingCommas"
    priority = 20

    def applies(self, context: Context) -> bool:
        # Heurística simple: buscar dos valores seguidos sin separador
        # Esto es complejo de detectar perfectamente sin un parser, 
        # pero buscamos patrones obvios: VALUE KEY o VALUE VALUE
        return True 

    def apply(self, context: Context):
        new_tokens = []
        
        # Definimos qué tokens pueden ser "fin de valor" y "inicio de clave/valor"
        value_enders = [TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.RBRACE, TokenType.RBRACKET, TokenType.BARE_WORD]
        value_starters = [TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.LBRACE, TokenType.LBRACKET, TokenType.BARE_WORD]
        
        for i, token in enumerate(context.tokens):
            new_tokens.append(token)
            
            if i + 1 < len(context.tokens):
                next_token = context.tokens[i+1]
                
                # Si tenemos (FinValor) (InicioValor) sin coma en medio
                if token.type in value_enders and next_token.type in value_starters:
                    # Excepción: key: value (BARE_WORD : ...)
                    # Si el siguiente es COLON, entonces el actual es una KEY, no un valor terminado.
                    # Pero aquí estamos mirando token actual y siguiente.
                    # Si token actual es KEY, debería venir COLON.
                    # Si token actual es VALUE, debería venir COMMA o RBRACE/RBRACKET.
                    
                    # Caso: "key": "val" "key2": "val"
                    # token="val" (STRING), next="key2" (STRING) -> Falta coma.
                    
                    # Caso: key: val key2: val
                    # token=val (BARE), next=key2 (BARE) -> Falta coma.
                    
                    # Debemos asegurarnos que no estamos insertando coma entre KEY y VALUE (ej "key" "value")
                    # Esto requiere mirar adelante si hay un COLON.
                    
                    is_next_a_key = False
                    if i + 2 < len(context.tokens):
                        if context.tokens[i+2].type == TokenType.COLON:
                            is_next_a_key = True
                    
                    # Si el siguiente parece ser una clave (porque le sigue un :), y el actual es un valor, falta coma.
                    if is_next_a_key:
                        # Insertar coma
                        new_tokens.append(Token(TokenType.COMMA, ",", ",", token.position + len(token.raw_value)))
                        context.record_rule(self.name)
                    
                    # Caso lista: [1 2 3]
                    # token=1, next=2. No hay colon. Ambos son valores.
                    # Necesitamos contexto de si estamos en lista u objeto?
                    # Por ahora, si dos literales están juntos y no hay colon cerca, asumimos lista y ponemos coma.
                    elif not is_next_a_key and token.type != TokenType.LBRACE and token.type != TokenType.LBRACKET:
                         # Evitar poner coma después de { o [
                         # Si next no es key, y current es valor...
                         # Riesgo: "key" "value" (sin dos puntos).
                         # Si insertamos coma: "key", "value". Mal.
                         # Si asumimos que falta dos puntos, es otra regla.
                         pass

        if len(new_tokens) > len(context.tokens):
            context.tokens = new_tokens

class TupleToListRule(Rule):
    """
    Convierte tuplas (..) en listas [..].
    """
    name = "TupleToList"
    priority = 15

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
