import copy
import difflib
from typing import List
from pyparsejson.core.context import Context
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


class RuleEngine:
    """
    Motor encargado de descubrir, instanciar y ejecutar reglas de reparación.
    Maneja la detección de cambios y la generación de reportes de diferencias (diffs).
    """

    @staticmethod
    def _generate_diff(old_str: str, new_str: str) -> str:
        """
        Genera un string unificado de diferencias para el reporte.
        Trunca el resultado si es excesivamente largo.
        """
        lines_old = old_str.splitlines(keepends=True)
        lines_new = new_str.splitlines(keepends=True)

        diff = difflib.unified_diff(lines_old, lines_new, n=1, lineterm='')
        diff_text = "".join(diff)

        if len(diff_text) > 200:
            return diff_text[:200] + "..."
        return diff_text

    @staticmethod
    def run_rules(context: Context, rules: List[Rule]) -> bool:
        """
        Ejecuta una lista de reglas secuencialmente sobre el contexto.

        Args:
            context: El contexto de reparación.
            rules: Lista de instancias de reglas a ejecutar.

        Returns:
            True si alguna regla modificó el contexto.
        """
        context.reset_changed_flag()

        for rule in rules:
            if rule.applies(context):
                # 1. Capturar estado previo
                # Nota: deepcopy puede ser costoso, pero es necesario para garantizar
                # la integridad del diff y la detección precisa de cambios estructurales.
                text_before = context.get_tokens_as_string()

                # 2. Ejecutar regla (mutación in-place)
                rule.apply(context)

                # 3. Verificar cambios
                text_after = context.get_tokens_as_string()

                if text_before != text_after:
                    context.mark_changed()
                    context.record_rule(rule.name)

                    diff_preview = RuleEngine._generate_diff(text_before, text_after)

                    # En modo Dry Run, registramos la modificación simulada.
                    # No revertimos el cambio en memoria para permitir que el motor
                    # converja hacia la solución final simulada.
                    if context.dry_run:
                        # Evitar duplicados en el log si la regla se aplica múltiples veces en el bucle
                        is_already_logged = any(m.rule_name == rule.name for m in context.report.modifications)
                        if not is_already_logged:
                            context.record_modification(rule.name, diff_preview)
                    else:
                        context.record_modification(rule.name, diff_preview)

        return context.changed

    @staticmethod
    def run_flow(context: Context, tags: List[str]) -> bool:
        """
        Ejecuta un conjunto de reglas basado en tags sobre el contexto.
        Las reglas se ordenan por prioridad antes de ejecutarse.

        Returns:
            True si al menos una regla aplicó cambios.
        """
        context.reset_changed_flag()

        rules_to_run = set()
        for tag in tags:
            for rule_cls in RuleRegistry.get_rules(tag):
                rules_to_run.add(rule_cls)

        # Instanciar y ordenar por prioridad (menor valor = mayor prioridad)
        sorted_rules = sorted([cls() for cls in rules_to_run], key=lambda r: r.priority)

        return RuleEngine.run_rules(context, sorted_rules)
