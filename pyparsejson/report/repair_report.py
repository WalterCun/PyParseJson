from dataclasses import dataclass, field
from typing import List, Optional, Any
from enum import Enum, auto


class RepairStatus(Enum):
    """Estado final del proceso de reparación."""
    SUCCESS_STRICT_JSON = auto()    # JSON válido y parseado correctamente sin advertencias
    SUCCESS_WITH_WARNINGS = auto()  # JSON válido, pero con calidad baja o parches agresivos
    PARTIAL_REPAIR = auto()         # No es JSON válido, pero se mejoró la estructura
    FAILED_UNRECOVERABLE = auto()   # No se pudo reparar o el input es ininteligible


@dataclass
class RepairAction:
    """
    Representa un cambio individual realizado por una regla específica.
    """
    rule_name: str
    description: str
    diff_preview: str  # Fragmento visual del cambio


@dataclass
class RepairReport:
    """
    Contiene toda la información sobre el resultado del proceso de reparación.
    """
    success: bool = False
    status: RepairStatus = RepairStatus.FAILED_UNRECOVERABLE
    
    # Resultados
    json_text: Optional[str] = None
    python_object: Optional[Any] = None
    
    # Métricas y detalles
    applied_rules: List[str] = field(default_factory=list)
    iterations: int = 0
    confidence: float = 0.0
    quality_score: float = 0.0
    
    # Errores y advertencias
    errors: List[str] = field(default_factory=list)
    detected_issues: List[str] = field(default_factory=list)

    # Auditoría detallada
    modifications: List[RepairAction] = field(default_factory=list)
    was_dry_run: bool = False
