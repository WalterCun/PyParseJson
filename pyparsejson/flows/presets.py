from pyparsejson.core.flow import Flow
from pyparsejson.core.context import Context

class MinimalJSONRepairFlow(Flow):
    """
    Flujo minimalista: Solo aplica correcciones estructurales críticas.
    Ideal para inputs que ya son casi JSON válido y se quiere evitar
    modificaciones agresivas en los valores.
    
    Tags ejecutados:
    - structure
    - pre_repair
    """
    def execute(self, context: Context) -> bool:
        # Solo reglas estructurales básicas
        return self.run_with_retries(context, tags=["structure", "pre_repair"])

class StandardJSONRepairFlow(Flow):
    """
    Flujo estándar: Combina reparación estructural y normalización básica de valores.
    Es el comportamiento recomendado para la mayoría de los casos.
    
    Tags ejecutados:
    - structure
    - pre_repair
    - values
    - normalization
    """
    def execute(self, context: Context) -> bool:
        # Estructura primero, luego valores, combinando el resultado
        changed1 = self.run_with_retries(context, tags=["structure", "pre_repair"])
        changed2 = self.run_with_retries(context, tags=["values", "normalization"])
        return changed1 or changed2

class AggressiveJSONRepairFlow(Flow):
    """
    Flujo agresivo: Intenta aplicar todas las reglas disponibles, incluyendo
    aquellas que podrían ser destructivas o inferir demasiado.
    Útil para 'Frankenstein JSONs' muy dañados.
    
    Tags ejecutados:
    - all (todas las reglas registradas)
    """
    def execute(self, context: Context) -> bool:
        # Ejecuta todo lo que encuentre en el registro
        return self.run_with_retries(context, tags=["all"])
