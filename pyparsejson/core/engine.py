from typing import List
from pyparsejson.core.context import Context
from pyparsejson.rules.registry import RuleRegistry

class RuleEngine:
    """
    Motor encargado de descubrir y ejecutar reglas.
    """
    def run_flow(self, context: Context, tags: List[str]) -> bool:
        """
        Ejecuta un conjunto de reglas basado en tags sobre el contexto.
        Retorna True si al menos una regla aplicó cambios.
        """
        context.reset_changed_flag() # Reiniciar al inicio del flujo

        rules_to_run = set()
        for tag in tags:
            for rule_cls in RuleRegistry.get_rules(tag):
                rules_to_run.add(rule_cls)
        
        sorted_rules = sorted([cls() for cls in rules_to_run], key=lambda r: r.priority)
        
        for rule in sorted_rules:
            if rule.applies(context):
                rule.apply(context)
        
        return context.changed
