# Path: pyparsejson\phases\tokenize.py
import re
from typing import List
from pyparsejson.core.token import Token, TokenType


class TolerantTokenizer:
    """
    Convierte un string de texto en una lista de tokens, siendo tolerante a errores
    y formatos no estándar de JSON.
    """

    # Patrones de tokens en orden de precedencia (más específico a más genérico)
    PATTERNS = [
        # === PATHS (MUST come FIRST to avoid fragmentation) ===
        # Unix paths: /var/www/html, /usr/local/bin
        # Windows paths: C:\Users\Admin, D:\Projects
        (TokenType.STRING, r'(?:[A-Za-z]:)?[/\\](?:[^\s:,\[\]\{\}"\'\)]+[/\\]?)+'),

        # URLs completas (DEBE ir ANTES de COLON para evitar fragmentación https:// → https + : + //)
        (TokenType.STRING, r'https?://[^\s"\'\]\}\),]+'),

        # Fechas y formatos especiales (antes de números para evitar 2026-01-01 → 2026 - 01 - 01)
        (TokenType.STRING, r'\d{4}-\d{2}-\d{2}'),
        (TokenType.STRING, r'\d{2}-\d{2}-\d{4}'),
        (TokenType.STRING, r'\d{3}-\d{4}'),
        (TokenType.STRING, r'\d{3}-\d{3}-\d{4}'),

        (TokenType.STRING, r'\d{3}-\d{4}'),  # Formato NNN-NNNN (555-0199)
        (TokenType.STRING, r'\d{3}-\d{3}-\d{4}'),  # Formato NNN-NNN-NNNN completo

        (TokenType.STRING, r'"(?:\\.|[^"\\])*"'),  # Comillas dobles
        (TokenType.STRING, r"'(?:\\.|[^'\\])*'"),  # Comillas simples

        # Números (antes de BARE_WORD para evitar fragmentación)
        (TokenType.NUMBER, r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'),

        # Booleanos y null
        (TokenType.BOOLEAN, r'\b(true|false|si|no|yes|on|off|1|0)\b'),
        (TokenType.NULL, r'\b(null|none|nil)\b'),

        # Estructuras
        (TokenType.LBRACE, r'\{'),
        (TokenType.RBRACE, r'\}'),
        (TokenType.LBRACKET, r'\['),
        (TokenType.RBRACKET, r'\]'),
        (TokenType.LPAREN, r'\('),
        (TokenType.RPAREN, r'\)'),

        # Separadores (DESPUÉS de URLs/fechas para no fragmentar)
        (TokenType.COLON, r':'),
        (TokenType.ASSIGN, r'='),
        (TokenType.COMMA, r','),

        # Palabras (último para evitar colisiones)
        (TokenType.BARE_WORD, r'[\wÀ-ÖØ-öø-ÿ][\w\-À-ÖØ-öø-ÿ]*'),

        # Cualquier otro caracter
        (TokenType.UNKNOWN, r'.'),
    ]

    def __init__(self):
        # Compilar regex una sola vez para eficiencia
        self.compiled_patterns = []
        for token_type, pattern in self.PATTERNS:
            flags = re.IGNORECASE if token_type in [TokenType.BOOLEAN, TokenType.NULL] else 0
            self.compiled_patterns.append((token_type, re.compile(pattern, flags)))

    def tokenize(self, text: str) -> List[Token]:
        """
        Procesa el texto y devuelve una lista de tokens.
        """
        tokens = []
        pos = 0
        line = 1
        column = 1
        while pos < len(text):
            # Saltar espacios en blanco y actualizar posición
            match_space = re.match(r'\s+', text[pos:])
            if match_space:
                whitespace = match_space.group(0)
                newlines = whitespace.count('\n')
                if newlines > 0:
                    line += newlines
                    column = len(whitespace.split('\n')[-1]) + 1
                else:
                    column += len(whitespace)
                pos += len(whitespace)
                continue

            # Encontrar el primer patrón que coincida
            match_found = False
            for token_type, regex in self.compiled_patterns:
                match = regex.match(text, pos)
                if match:
                    value = match.group(0)
                    # Evitar que BARE_WORD capture un punto solitario
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

            # Si no se encuentra ninguna coincidencia, avanzar para evitar bucle infinito
            if not match_found:
                pos += 1
                column += 1

        return tokens