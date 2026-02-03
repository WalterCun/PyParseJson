from dataclasses import dataclass, field
from typing import List, Optional
from pyparsejson.core.token import Token
from pyparsejson.report.repair_report import RepairReport, RepairModification

@dataclass
class Context:
    """
    Contenedor de estado para el proceso de reparación.
    Mantiene la lista de tokens y el reporte de cambios.
    """
    initial_text: str
    tokens: List[Token] = field(default_factory=list)
    report: RepairReport = field(default_factory=RepairReport)
    max_iterations: int = 10
    current_iteration: int = 0
    dry_run: bool = False
    _changed: bool = False

    @property
    def changed(self) -> bool:
        return self._changed

    def mark_changed(self):
        self._changed = True

    def reset_changed_flag(self):
        self._changed = False

    def record_rule(self, rule_name: str):
        if rule_name not in self.report.applied_rules:
            self.report.applied_rules.append(rule_name)

    def record_modification(self, rule_name: str, diff: str):
        mod = RepairModification(rule_name=rule_name, diff=diff)
        self.report.modifications.append(mod)

    def get_tokens_as_string(self) -> str:
        return "".join(t.value for t in self.tokens)
