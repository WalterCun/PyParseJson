import copy
import difflib
from typing import List
from pyparsejson.core.context import Context
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


class RuleEngine:
    """
    Motor encargado de descubrir y ejecutar reglas con capacidad de auditoría (Dry Run).
    """

    @staticmethod
    def _generate_diff(old_str: str, new_str: str) -> str:
        """Genera un string unificado de diferencias."""
        lines_old = old_str.splitlines(keepends=True)
        lines_new = new_str.splitlines(keepends=True)

        # Usamos difflib estándar
        diff = difflib.unified_diff(lines_old, lines_new, n=1, lineterm='')

        # Si es muy largo, acortamos para el reporte
        diff_text = "".join(diff)
        if len(diff_text) > 200:
            return diff_text[:200] + "..."
        return diff_text

    @staticmethod
    def run_rules(context: Context, rules: List[Rule]) -> bool:
        context.reset_changed_flag()

        for rule in rules:
            if rule.applies(context):
                # 1. TOMAR INSTANTÁNEA ANTES
                tokens_snapshot = copy.deepcopy(context.tokens)
                text_before = context.get_tokens_as_string()

                # 2. EJECUTAR REGLA
                rule.apply(context)

                # 3. VERIFICAR CAMBIOS
                text_after = context.get_tokens_as_string()

                if text_before != text_after:
                    # Hubo cambios
                    context.mark_changed()
                    context.record_rule(rule.name)

                    # Generar diff
                    diff_preview = RuleEngine._generate_diff(text_before, text_after)

                    # --- LÓGICA DE DRY RUN (CORREGIDA) ---
                    # En modo Dry Run, NO revertimos el contexto. Permitimos que el motor converja
                    # para ver el resultado final simulado. Solo limitamos el registro de logs.

                    if context.dry_run:
                        # Evitar spam de logs: Solo registrar cada regla una vez en la lista de modificaciones
                        is_already_logged = any(m.rule_name == rule.name for m in context.report.modifications)

                        if not is_already_logged:
                            context.record_modification(rule.name, diff_preview)
                    else:
                        # En modo normal, registramos todo (o podríamos aplicar lógica diferente)
                        context.record_modification(rule.name, diff_preview)

                    # Si NO es dry run, aquí podríamos hacer lógica de commit.
                    # Como Dry Run es solo lectura para el usuario final (simulación),
                    # dejamos el contexto modificado para que el motor pueda seguir trabajando
                    # y llegar al resultado final (esto soluciona el problema del bucle infinito).

        return context.changed

    @staticmethod
    def run_flow(context: Context, tags: List[str]) -> bool:
        """
        Ejecuta un conjunto de reglas basado en tags sobre el contexto.
        Retorna True si al menos una regla aplicó cambios.
        """
        context.reset_changed_flag()

        rules_to_run = set()
        for tag in tags:
            for rule_cls in RuleRegistry.get_rules(tag):
                rules_to_run.add(rule_cls)

        sorted_rules = sorted([cls() for cls in rules_to_run], key=lambda r: r.priority)

        return RuleEngine.run_rules(context, sorted_rules)