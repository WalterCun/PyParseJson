from abc import ABC, abstractmethod
from typing import List, Optional
from pyparsejson.core.context import Context
from pyparsejson.core.engine import RuleEngine
from pyparsejson.core.rule_selector import RuleSelector


class Flow(ABC):
    """
    Clase base abstracta que representa una etapa lógica en el pipeline de reparación.
    Un flujo agrupa un conjunto de reglas y define cómo deben ejecutarse.
    """

    def __init__(self, engine: RuleEngine):
        self.engine = engine
        self.max_passes = 10  # Límite de iteraciones internas por flujo para evitar bucles infinitos
        self.selector: Optional[RuleSelector] = None

    @abstractmethod
    def execute(self, context: Context) -> bool:
        """
        Ejecuta la lógica del flujo sobre el contexto dado.

        Args:
            context: El contexto actual de reparación.

        Returns:
            True si el flujo realizó algún cambio en el contexto, False en caso contrario.
        """
        pass

    def run_with_retries(self, context: Context, tags: List[str]) -> bool:
        """
        Ejecuta reglas seleccionadas por tags iterativamente mientras sigan produciendo cambios.

        Args:
            context: El contexto de reparación.
            tags: Lista de tags para seleccionar las reglas del registro.

        Returns:
            True si hubo algún cambio en cualquiera de las pasadas.
        """
        flow_changed = False
        for _ in range(self.max_passes):
            changed_this_pass = self.engine.run_flow(context, tags)
            if changed_this_pass:
                flow_changed = True
            else:
                # Si el motor no reportó ningún cambio en esta pasada, el estado es estable
                break
        return flow_changed

    def run(self, context: Context) -> bool:
        """
        Ejecuta las reglas definidas en el `self.selector` de este flujo.

        Returns:
            True si hubo cambios.
        """
        if not self.selector:
            return False

        changed = False
        
        # Resolvemos las clases de reglas y las instanciamos
        rule_classes = self.selector.resolve()
        rules = [cls() for cls in rule_classes]

        for _ in range(self.max_passes):
            if self.engine.run_rules(context, rules):
                changed = True
            else:
                break

        return changed
