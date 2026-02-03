from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Any

class RepairStatus(Enum):
    SUCCESS_STRICT_JSON = auto()
    SUCCESS_WITH_WARNINGS = auto()
    SUCCESS_EMPTY_INPUT = auto()
    PARTIAL_REPAIR = auto()
    FAILED_UNRECOVERABLE = auto()
    FAILURE_NO_STRUCTURE = auto()

@dataclass
class RepairModification:
    """Representa un cambio específico realizado por una regla."""
    rule_name: str
    diff: str

@dataclass
class RepairReport:
    success: bool = False
    status: Optional[RepairStatus] = None
    json_text: str = ""
    python_object: Optional[Any] = None
    quality_score: float = 0.0
    iterations: int = 0
    applied_rules: List[str] = field(default_factory=list)
    modifications: List[RepairModification] = field(default_factory=list)
    detected_issues: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    was_dry_run: bool = False
