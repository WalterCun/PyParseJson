import re
from typing import List
from pyparsejson.core.token import Token, TokenType


class TolerantTokenizer:
    """
    Convierte texto en una lista de tokens, siendo tolerante a errores.
    """

    # Patrones de tokens
    # Formato: (TokenType, Regex Pattern)
    # EL ORDEN IMPORTA: Patrones más específicos van antes de los genéricos.
    PATTERNS = [
        (TokenType.STRING, r'"(?:\\.|[^"\\])*"'),  # Strings con comillas dobles
        (TokenType.STRING, r"'(?:\\.|[^'\\])*'"),  # Strings con comillas simples (tolerante)

        # --- PATRONES ESPECÍFICOS ---
        # FECHA: Usamos \b (word boundary) en lugar de look-behinds.
        (TokenType.DATE, r'\b\d{4}-\d{2}-\d{2}\b'),

        (TokenType.NUMBER, r'-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?'),
        (TokenType.BOOLEAN, r'\b(true|false|si|no|yes|on|off)\b'),
        (TokenType.NULL, r'\b(null|none|nil)\b'),
        (TokenType.LBRACE, r'\{'),
        (TokenType.RBRACE, r'\}'),
        (TokenType.LBRACKET, r'\['),
        (TokenType.RBRACKET, r'\]'),
        (TokenType.LPAREN, r'\('),
        (TokenType.RPAREN, r'\)'),
        (TokenType.COLON, r':'),
        (TokenType.ASSIGN, r'='),
        (TokenType.COMMA, r','),

        # Bare words: Se añaden rangos de caracteres acentuados para soporte básico UTF-8
        # CORRECCIÓN: Agregamos guiones - para soportar teléfonos
        (TokenType.BARE_WORD, r'[\wÀ-ÖØ-öø-ÿ][\w\-À-ÖØ-öø-ÿ]*'),
        (TokenType.UNKNOWN, r'.'),  # Cualquier otro caracter
    ]

    def tokenize(self, text: str) -> List[Token]:
        tokens = []
        pos = 0
        line = 1
        column = 1

        # Compilamos todas las regex una sola vez para eficiencia
        COMPILED_PATTERNS = []
        for token_type, pattern in self.PATTERNS:
            flags = re.IGNORECASE if token_type in [TokenType.BOOLEAN, TokenType.NULL] else 0
            COMPILED_PATTERNS.append((token_type, re.compile(pattern, flags)))

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
            for token_type, regex in COMPILED_PATTERNS:
                match = regex.match(text, pos)

                if match:
                    value = match.group(0)

                    # Evitar que BARE_WORD capture solo un punto.
                    if token_type == TokenType.BARE_WORD and value == ".":
                        continue

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
                # Safety break para evitar loop infinito
                pos += 1
                column += 1

        return tokens