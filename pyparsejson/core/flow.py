from abc import ABC, abstractmethod
from typing import List
from pyparsejson.core.context import Context
from pyparsejson.core.engine import RuleEngine

class Flow(ABC):
    """
    Representa una etapa lógica en el pipeline de reparación.
    """
    def __init__(self, engine: RuleEngine):
        self.engine = engine

    @abstractmethod
    def execute(self, context: Context):
        pass

class PreRepairFlow(Flow):
    """
    Flujo inicial: Estructura básica y limpieza.
    """
    def execute(self, context: Context):
        self.engine.run_flow(context, tags=["pre_repair", "structure"])

class ValueNormalizationFlow(Flow):
    """
    Flujo secundario: Normalización de valores y tipos.
    """
    def execute(self, context: Context):
        self.engine.run_flow(context, tags=["values", "normalization"])

class FinalizationFlow(Flow):
    """
    Flujo final: Preparación para JSON estricto.
    """
    def execute(self, context: Context):
        # Aquí podríamos tener reglas de limpieza final o validación ligera
        pass
