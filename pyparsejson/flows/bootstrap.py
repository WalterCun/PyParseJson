from pyparsejson.core.flow import Flow
from pyparsejson.core.context import Context

class BootstrapRepairFlow(Flow):
    """
    Flujo de arranque OBLIGATORIO.
    Se encarga de las reparaciones estructurales más críticas que habilitan
    el funcionamiento del resto de las reglas.
    """
    def __init__(self, engine):
        super().__init__(engine)
        self.max_passes = 5 

    def execute(self, context: Context) -> bool:
        """
        Ejecuta reglas estructurales críticas repetidamente.
        Incluye WrapRootObjectRule (priority=1) que es vital.
        Devuelve True si hubo cambios.
        """
        return self.run_with_retries(context, tags=["structure", "pre_repair"])
