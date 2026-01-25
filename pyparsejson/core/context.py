from typing import List, Optional
from pyparsejson.core.token import Token
from pyparsejson.models.repair_report import Report

class Context:
    """
    Mantiene el estado del proceso de parsing y reparación.
    """
    def __init__(self, raw_text: str):
        self.raw_text = raw_text
        self.tokens: List[Token] = []
        self.report = Report()
        self.current_iteration = 0
        self.max_iterations = 10
        self.changed_in_last_pass = False

    def record_rule(self, rule_name: str):
        self.report.applied_rules.append(rule_name)
        self.changed_in_last_pass = True

    def get_tokens_as_string(self) -> str:
        """Reconstruye el texto a partir de los tokens actuales."""
        # Esta es una reconstrucción simple, idealmente se manejaría espaciado
        return "".join(t.raw_value for t in self.tokens)
