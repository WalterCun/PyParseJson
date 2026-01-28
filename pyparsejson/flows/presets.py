from pyparsejson.core.context import Context
from pyparsejson.core.flow import Flow
from pyparsejson.core.rule_selector import RuleSelector


class MinimalJSONRepairFlow(Flow):
    """
    Flujo minimalista: Solo aplica correcciones estructurales críticas.
    Ideal para inputs que ya son casi JSON válido y se quiere evitar
    modificaciones agresivas en los valores.
    """

    def execute(self, context: Context) -> bool:
        return self.run_with_retries(context, tags=["structure", "pre_repair"])


class StandardJSONRepairFlow(Flow):
    """
    Flujo estándar: Combina reparación estructural y normalización básica de valores.
    Es el comportamiento recomendado para la mayoría de los casos.
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.selector = (
            RuleSelector()
            .add_tags("structure", "pre_repair", "values", "smart", "normalization", "cleanup")
        )

    def execute(self, context: Context) -> bool:
        return self.run(context)


class AggressiveJSONRepairFlow(Flow):
    """
    Flujo agresivo: Intenta aplicar todas las reglas disponibles, incluyendo
    aquellas que podrían ser destructivas o inferir demasiado.
    Útil para 'Frankenstein JSONs' muy dañados.
    """

    def execute(self, context: Context) -> bool:
        return self.run_with_retries(context, tags=["all"])
