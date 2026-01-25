from abc import ABC, abstractmethod

class Rule(ABC):
    """
    Clase base para todas las reglas de reparación y normalización.
    """
    priority = 100  # Prioridad por defecto (menor número = mayor prioridad)
    name = "BaseRule"

    @abstractmethod
    def applies(self, context) -> bool:
        """
        Determina si la regla debe aplicarse al contexto actual.
        """
        pass

    @abstractmethod
    def apply(self, context):
        """
        Aplica la regla modificando el contexto.
        """
        pass
