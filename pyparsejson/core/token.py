from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    """Tipos de tokens soportados por el analizador léxico."""
    LBRACE = auto()    # {
    RBRACE = auto()    # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    COLON = auto()     # :
    COMMA = auto()     # ,
    STRING = auto()    # "foo", 'foo'
    NUMBER = auto()    # 123, 12.34, 1e5
    BOOLEAN = auto()   # true, false
    NULL = auto()      # null
    BARE_WORD = auto() # foo (identificadores sin comillas)
    ASSIGN = auto()    # =
    LPAREN = auto()    # (
    RPAREN = auto()    # )
    DATE = auto()      # 2026-01-01
    UNKNOWN = auto()   # Caracteres no reconocidos


@dataclass
class Token:
    """
    Representa una unidad léxica (token) extraída del texto fuente.
    """
    type: TokenType
    value: str
    raw_value: str
    position: int
    line: int = 0
    column: int = 0

    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}')"
