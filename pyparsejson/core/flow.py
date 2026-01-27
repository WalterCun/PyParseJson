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
        self.max_passes = 10  # Límite de iteraciones internas por flujo
        self.selector = None

    @abstractmethod
    def execute(self, context: Context) -> bool:
        """
        Ejecuta la lógica del flujo y devuelve True si hubo cambios.
        """
        pass

    def run_with_retries(self, context: Context, tags: List[str]) -> bool:
        """
        Helper para ejecutar reglas iterativamente mientras haya cambios.
        Devuelve True si hubo algún cambio en cualquiera de las pasadas.
        """
        flow_changed = False
        for _ in range(self.max_passes):
            changed_this_pass = self.engine.run_flow(context, tags)
            if changed_this_pass:
                flow_changed = True
            else:
                # Si el motor no reportó ningún cambio en esta pasada, salimos del bucle
                break
        return flow_changed

    def run(self, context: Context) -> bool:
        changed = False

        # --- CORRECCIÓN AQUÍ ---
        # resolve() devuelve las CLASES de reglas, pero run_rules necesita INSTANCIAS.
        raw_rules = self.selector.resolve()
        rules = [cls() for cls in raw_rules]
        # ------------------------

        for _ in range(self.max_passes):
            if self.engine.run_rules(context, rules):
                changed = True
            else:
                break

        return changed