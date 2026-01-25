import re
from typing import List
from pyparsejson.core.token import Token, TokenType

class TolerantTokenizer:
    """
    Convierte texto en una lista de tokens, siendo tolerante a errores.
    """
    
    # Patrones de tokens
    PATTERNS = [
        (TokenType.STRING, r'"(?:\\.|[^"\\])*"'),  # Strings con comillas dobles
        (TokenType.STRING, r"'(?:\\.|[^'\\])*'"),  # Strings con comillas simples (tolerante)
        (TokenType.NUMBER, r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?'),
        (TokenType.BOOLEAN, r'\b(true|false|si|no|yes|on|off)\b', re.IGNORECASE),
        (TokenType.NULL, r'\b(null|none|nil)\b', re.IGNORECASE),
        (TokenType.LBRACE, r'\{'),
        (TokenType.RBRACE, r'\}'),
        (TokenType.LBRACKET, r'\['),
        (TokenType.RBRACKET, r'\]'),
        (TokenType.LPAREN, r'\('),
        (TokenType.RPAREN, r'\)'),
        (TokenType.COLON, r':'),
        (TokenType.ASSIGN, r'='),
        (TokenType.COMMA, r','),
        # Bare words: identificadores sin comillas, incluyendo fechas simples o palabras compuestas
        (TokenType.BARE_WORD, r'[a-zA-Z_][a-zA-Z0-9_\-\.]*'), 
        (TokenType.UNKNOWN, r'.'), # Cualquier otro caracter (espacios se manejan aparte)
    ]

    def tokenize(self, text: str) -> List[Token]:
        tokens = []
        pos = 0
        line = 1
        column = 1
        
        while pos < len(text):
            # Saltar espacios en blanco pero mantener conteo de líneas
            match_space = re.match(r'\s+', text[pos:])
            if match_space:
                whitespace = match_space.group(0)
                newlines = whitespace.count('\n')
                line += newlines
                if newlines > 0:
                    column = 1 + len(whitespace.split('\n')[-1])
                else:
                    column += len(whitespace)
                pos += len(whitespace)
                continue

            match_found = False
            for token_type, pattern in self.PATTERNS:
                # Usamos flags=re.IGNORECASE solo para boolean/null si se requiere, 
                # pero aquí compilamos regex específicas.
                # Para simplificar, pasamos flags en el match si es necesario o definimos patrones inteligentes.
                
                flags = re.IGNORECASE if token_type in [TokenType.BOOLEAN, TokenType.NULL] else 0
                regex = re.compile(pattern, flags)
                match = regex.match(text, pos)
                
                if match:
                    value = match.group(0)
                    # Ajuste para strings: quitar comillas si es STRING
                    # Pero guardamos raw_value tal cual
                    
                    tokens.append(Token(
                        type=token_type,
                        value=value,
                        raw_value=value,
                        position=pos,
                        line=line,
                        column=column
                    ))
                    
                    pos += len(value)
                    column += len(value)
                    match_found = True
                    break
            
            if not match_found:
                # Safety break para evitar loop infinito si algo falla catastróficamente
                # (aunque UNKNOWN debería atrapar todo)
                pos += 1
                column += 1
                
        return tokens
