from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict

@dataclass
class RepairReport:
    success: bool = False
    json_text: Optional[str] = None
    python_object: Optional[Any] = None
    applied_rules: List[str] = field(default_factory=list)
    iterations: int = 0
    confidence: float = 0.0
    errors: List[str] = field(default_factory=list)
