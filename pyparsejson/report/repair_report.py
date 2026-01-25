from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum, auto

class RepairStatus(Enum):
    SUCCESS_STRICT_JSON = auto()    # JSON válido y parseado correctamente
    PARTIAL_REPAIR = auto()         # No es JSON válido, pero se mejoró la estructura
    FAILED_UNRECOVERABLE = auto()   # No se pudo reparar o el input es ininteligible

@dataclass
class RepairReport:
    success: bool = False
    status: RepairStatus = RepairStatus.FAILED_UNRECOVERABLE
    json_text: Optional[str] = None
    python_object: Optional[Any] = None
    applied_rules: List[str] = field(default_factory=list)
    iterations: int = 0
    confidence: float = 0.0
    quality_score: float = 0.0
    errors: List[str] = field(default_factory=list)
    detected_issues: List[str] = field(default_factory=list)
