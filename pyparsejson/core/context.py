from typing import List
from pyparsejson.core.token import Token
from pyparsejson.report.repair_report import RepairReport, RepairAction


class Context:
    """
    Mantiene el estado global del proceso de parsing y reparación.
    Contiene los tokens actuales, el reporte de progreso y configuración de ejecución.
    """

    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.tokens: List[Token] = []
        self.report = RepairReport()
        
        # Control de iteraciones
        self.current_iteration = 0
        self.max_iterations = 10
        self.changed = False

        # Configuración de auditoría
        self.dry_run = False
        self.original_raw_text = raw_text

    def mark_changed(self):
        """Marca que el contexto ha sido modificado en la iteración actual."""
        self.changed = True

    def record_rule(self, rule_name: str):
        """Registra el nombre de una regla aplicada en el reporte."""
        if rule_name not in self.report.applied_rules:
            self.report.applied_rules.append(rule_name)

    def record_modification(self, rule_name: str, diff_preview: str):
        """Registra una acción de modificación detallada en el reporte."""
        action = RepairAction(
            rule_name=rule_name,
            description=f"Applied changes via {rule_name}",
            diff_preview=diff_preview
        )
        self.report.modifications.append(action)

    def reset_changed_flag(self):
        """Reinicia el indicador de cambios para una nueva pasada."""
        self.changed = False

    def get_tokens_as_string(self) -> str:
        """
        Reconstruye el texto completo a partir de la lista actual de tokens.
        Útil para generar diffs y verificar el estado del texto.
        """
        return "".join(t.raw_value for t in self.tokens)
