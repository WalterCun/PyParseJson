from abc import ABC, abstractmethod
from typing import List
from pyparsejson.core.context import Context

class Rule(ABC):
    """
    Clase base para todas las reglas de reparación.
    """
    priority: int = 100
    tags: List[str] = []
    name: str = "BaseRule"

    def __init__(self):
        # El nombre por defecto es el nombre de la clase
        self.name = self.__class__.__name__

    @abstractmethod
    def applies(self, context: Context) -> bool:
        """Determina si la regla debe ejecutarse."""
        pass

    @abstractmethod
    def apply(self, context: Context):
        """Modifica la lista de tokens en el contexto."""
        pass
