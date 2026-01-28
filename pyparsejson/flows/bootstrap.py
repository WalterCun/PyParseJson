from pyparsejson.core.context import Context
from pyparsejson.core.flow import Flow


class BootstrapRepairFlow(Flow):
    """
    Flujo de arranque OBLIGATORIO.
    Se encarga de las reparaciones estructurales más críticas que habilitan
    el funcionamiento del resto de las reglas (ej: asegurar que haya un objeto raíz).
    """
    immutable = True

    def __init__(self, engine):
        super().__init__(engine)
        self.max_passes = 5

    def execute(self, context: Context) -> bool:
        """
        Ejecuta reglas estructurales críticas repetidamente.
        """
        return self.run_with_retries(context, tags=["structure", "pre_repair"])
