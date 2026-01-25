from typing import List, Type
from pyparsejson.core.context import Context
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry

class RuleEngine:
    """
    Motor encargado de descubrir y ejecutar reglas.
    """
    def __init__(self):
        self.loaded_rules = {}

    def get_rules_by_tag(self, tag: str) -> List[Rule]:
        """Instancia y devuelve reglas asociadas a un tag, ordenadas por prioridad."""
        rule_classes = RuleRegistry.get_rules(tag)
        return [cls() for cls in rule_classes]

    def run_flow(self, context: Context, tags: List[str]):
        """Ejecuta un conjunto de reglas basado en tags sobre el contexto."""
        # Recolectar reglas únicas de todos los tags
        rules_to_run = set()
        for tag in tags:
            for rule_cls in RuleRegistry.get_rules(tag):
                rules_to_run.add(rule_cls)
        
        # Ordenar por prioridad
        sorted_rules = sorted([cls() for cls in rules_to_run], key=lambda r: r.priority)
        
        # Ejecutar
        for rule in sorted_rules:
            if rule.applies(context):
                rule.apply(context)
