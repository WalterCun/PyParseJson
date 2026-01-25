from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional

class TokenType(Enum):
    LBRACE = auto()    # {
    RBRACE = auto()    # }
    LBRACKET = auto()  # [
    RBRACKET = auto()  # ]
    COLON = auto()     # :
    COMMA = auto()     # ,
    STRING = auto()    # "foo"
    NUMBER = auto()    # 123, 12.34
    BOOLEAN = auto()   # true, false
    NULL = auto()      # null
    BARE_WORD = auto() # foo (sin comillas)
    ASSIGN = auto()    # =
    LPAREN = auto()    # (
    RPAREN = auto()    # )
    UNKNOWN = auto()   # caracteres no reconocidos

@dataclass
class Token:
    type: TokenType
    value: str
    raw_value: str
    position: int
    line: int = 0
    column: int = 0
    
    def __repr__(self):
        return f"Token({self.type.name}, '{self.value}')"
