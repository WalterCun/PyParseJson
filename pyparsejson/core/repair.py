import json
from typing import List, Optional

from pyparsejson.core.context import Context
from pyparsejson.core.engine import RuleEngine
from pyparsejson.core.flow import Flow

from pyparsejson.flows.presets import StandardJSONRepairFlow
from pyparsejson.flows.bootstrap import BootstrapRepairFlow

from pyparsejson.phases.pre_normalize import PreNormalizeText
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.phases.json_finalize import JSONFinalize

from pyparsejson.report.repair_report import RepairReport, RepairStatus
from pyparsejson.core.quality import RepairQualityEvaluator
from pyparsejson.core.token import TokenType


class Repair:
    """
    Orquestador principal del proceso de reparación de JSON.
    """

    def __init__(self, auto_flows: bool = True, dry_run: bool = False):
        self.engine = RuleEngine()
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.finalizer = JSONFinalize()
        self.quality_evaluator = RepairQualityEvaluator()

        # Configuración por defecto
        self.dry_run = dry_run

        # Flujo de arranque (SIEMPRE se ejecuta primero)
        self.bootstrap_flow = BootstrapRepairFlow(self.engine)

        self.user_flows: List[Flow] = []
        if auto_flows:
            self.add_flow(StandardJSONRepairFlow(self.engine))

    def add_flow(self, flow: Flow):
        if not hasattr(flow, "engine") or flow.engine is None:
            flow.engine = self.engine
        self.user_flows.append(flow)

    def parse(self, text: str, dry_run: Optional[bool] = None) -> RepairReport:
        """
        Ejecuta el proceso de reparación.

        Args:
            text: El texto a reparar.
            dry_run (optional):
                - Si es True: Ejecuta en modo auditoría (sin afectar nada externamente).
                - Si es False: Ejecuta normal.
                - Si es None (Default): Usa la configuración definida en el constructor.
        """
        # Lógica de prioridad: El argumento del método sobrescribe al del constructor
        effective_dry_run = self.dry_run if dry_run is None else dry_run

        return self._run(text, dry_run=effective_dry_run)

    def _run(self, text: str, dry_run: bool = False) -> RepairReport:
        """
        Método interno compartido por parse() (usando configuración de instancia o override).
        """
        # 1. Pre-normalización y tokenización
        clean_text = self.pre_normalize.process(text)
        context = Context(clean_text)

        # Si el texto está completamente vacío después de limpiar
        if not clean_text:
            return RepairReport(
                success=True,
                status=RepairStatus.SUCCESS_STRICT_JSON,
                json_text="{}",
                python_object={}
            )

        context.tokens = self.tokenizer.tokenize(clean_text)

        # Activar modo Dry Run basado en la decisión tomada en parse()
        context.dry_run = dry_run
        context.report.was_dry_run = dry_run

        success = False
        python_obj = None

        # 2. Repair loop iterativo
        while context.current_iteration < context.max_iterations:
            context.current_iteration += 1
            any_changed_in_iteration = False

            # 2.1 Bootstrap flow (siempre primero)
            bootstrap_changed = self.bootstrap_flow.execute(context)
            any_changed_in_iteration |= bootstrap_changed

            # 2.2 User / standard flows
            for flow in self.user_flows:
                flow_changed = flow.execute(context)
                any_changed_in_iteration |= flow_changed

            # 2.3 Si no hubo cambios → estado estable
            if not any_changed_in_iteration:
                break

        # 3. Finalización y parseo JSON real
        final_json = self.finalizer.process(context)

        try:
            python_obj = json.loads(final_json)
            success = True
        except json.JSONDecodeError as e:
            context.report.errors.append(str(e))

        # --- NUEVO: FALLBACK A {} ---
        # Si falló el parseo estricto, verificamos si es "basura pura" (no raíz { o [).
        # Si es basura, devolvemos un objeto vacío para no romper aplicaciones que esperan un dict.
        if not success:
            if not context.tokens or context.tokens[0].type not in (TokenType.LBRACE, TokenType.LBRACKET):
                final_json = "{}"
                python_obj = {}
                success = True
                # Marcamos que fue un parche (simulación de éxito)
                context.report.detected_issues.append("Devuelve {} por falta de estructura raíz válida.")
        # ------------------------------

        # 4. Evaluación de calidad
        quality_score, issues = self.quality_evaluator.evaluate(context)

        # 5. Construcción del reporte final
        context.report.success = success
        context.report.quality_score = quality_score
        context.report.detected_issues = issues
        context.report.json_text = final_json
        context.report.python_object = python_obj
        context.report.iterations = context.current_iteration

        # 6. Estado final
        if success:
            if quality_score < 1.0:
                context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
            else:
                context.report.status = RepairStatus.SUCCESS_STRICT_JSON
        else:
            # Si forzamos el parche a {}, se marca como éxito, pero es bueno saberlo
            if python_obj == {} and context.report.detected_issues:
                # Es técnicamente un parche de éxito
                context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
            elif context.report.applied_rules:
                context.report.status = RepairStatus.PARTIAL_REPAIR
            else:
                context.report.status = RepairStatus.FAILED_UNRECOVERABLE

        return context.report