from typing import List, Optional
from pyparsejson.core.token import Token
from pyparsejson.report.repair_report import RepairReport

class Context:
    """
    Mantiene el estado del proceso de parsing y reparación.
    """
    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.tokens: List[Token] = []
        self.report = RepairReport()
        self.current_iteration = 0
        self.max_iterations = 10
        self.changed = False

    def mark_changed(self):
        """
        Marca que el contexto ha sido modificado en la pasada actual.
        """
        self.changed = True

    def record_rule(self, rule_name: str):
        """
        Registra que una regla ha sido aplicada.
        """
        if rule_name not in self.report.applied_rules:
            self.report.applied_rules.append(rule_name)

    def reset_changed_flag(self):
        """
        Reinicia el flag de cambios para una nueva iteración.
        """
        self.changed = False

    def get_tokens_as_string(self) -> str:
        """Reconstruye el texto a partir de los tokens actuales."""
        return "".join(t.raw_value for t in self.tokens)
