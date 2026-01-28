from abc import ABC, abstractmethod
from typing import List
from pyparsejson.core.context import Context


class Rule(ABC):
    """
    Clase base abstracta para todas las reglas de reparación.
    Cada regla encapsula una lógica específica para detectar y corregir
    un patrón de error en la secuencia de tokens.
    """
    priority: int = 100
    tags: List[str] = []
    name: str = "BaseRule"

    def __init__(self):
        # El nombre por defecto es el nombre de la clase
        self.name = self.__class__.__name__

    @abstractmethod
    def applies(self, context: Context) -> bool:
        """
        Determina si la regla debe ejecutarse en el contexto actual.
        Debe ser una comprobación rápida y sin efectos secundarios.
        """
        pass

    @abstractmethod
    def apply(self, context: Context):
        """
        Aplica la corrección modificando la lista de tokens en el contexto.
        Esta operación es destructiva (in-place).
        """
        pass
