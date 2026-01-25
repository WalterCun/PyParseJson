from abc import ABC, abstractmethod
from pyparsejson.core.context import Context

class Rule(ABC):
    """
    Clase base para todas las reglas de reparación.
    """
    priority = 100
    name = "BaseRule"

    @abstractmethod
    def applies(self, context: Context) -> bool:
        """Determina si la regla debe ejecutarse."""
        pass

    @abstractmethod
    def apply(self, context: Context):
        """Modifica la lista de tokens en el contexto."""
        pass
