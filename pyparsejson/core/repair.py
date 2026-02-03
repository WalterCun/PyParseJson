import json
import logging
import re
from typing import List, Optional, Any

from pyparsejson.core.context import Context
from pyparsejson.core.engine import RuleEngine
from pyparsejson.core.flow import Flow
from pyparsejson.core.quality import RepairQualityEvaluator
from pyparsejson.core.token import TokenType, Token
from pyparsejson.flows.bootstrap import BootstrapRepairFlow
from pyparsejson.flows.presets import StandardJSONRepairFlow
from pyparsejson.phases.json_finalize import JSONFinalize
from pyparsejson.phases.pre_normalize import PreNormalizeText
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.report.repair_report import RepairReport, RepairStatus
from pyparsejson.utils.logger import RepairLogger


class Repair:
    """
    Orquestador principal del proceso de reparación de JSON.
    Coordina las fases de normalización, tokenización, aplicación de reglas y finalización.
    """

    def __init__(self, auto_flows: bool = True, dry_run: bool = False, debug: bool = False,
                 log_level: int = logging.WARNING, mode: str = "lax"):
        """
        Inicializa el motor de reparación.

        Args:
            auto_flows: Si es True, carga los flujos de reparación estándar.
            dry_run: Si es True, ejecuta en modo auditoría sin aplicar cambios finales.
            debug: Si es True, imprime información de debugging.
            mode: "lax" (default) devuelve {} si falla. "strict" lanza excepción.
        """
        self.engine = RuleEngine()
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.logger = RepairLogger("pyparsejson.repair", level=log_level)
        self.finalizer = JSONFinalize(log_level)
        self.quality_evaluator = RepairQualityEvaluator()

        self.dry_run = dry_run
        self.debug = debug
        self.mode = mode

        self.bootstrap_flow = BootstrapRepairFlow(self.engine)

        self.user_flows: List[Flow] = []
        if auto_flows:
            self.add_flow(StandardJSONRepairFlow(self.engine))

    def _debug_log(self, message: str):
        if self.debug:
            print(f"[DEBUG] {message}")

    def _run(self, text: str, dry_run: bool = False) -> RepairReport:
        clean_text = self.pre_normalize.process(text)
        self._debug_log(f"Pre-normalized text: {clean_text[:100]}...")

        if not clean_text:
            return RepairReport(
                success=True,
                status=RepairStatus.SUCCESS_EMPTY_INPUT,
                json_text="{}",
                python_object={},
                quality_score=0.0,
                iterations=0,
                applied_rules=[]
            )

        context = Context(clean_text)
        context.tokens = self.tokenizer.tokenize(clean_text)
        context.dry_run = dry_run
        context.report.was_dry_run = dry_run

        self._debug_log(
            f"Initial tokens ({len(context.tokens)}): {[f'{t.type.name}:{t.value}' for t in context.tokens[:10]]}")

        has_structure = any(t.type in (TokenType.LBRACE, TokenType.LBRACKET, TokenType.COLON, TokenType.ASSIGN)
                            for t in context.tokens)

        if not has_structure:
            self._debug_log("No structure detected, returning empty object")
            return RepairReport(
                success=False,
                status=RepairStatus.FAILURE_NO_STRUCTURE,
                json_text="{}",
                python_object={},
                quality_score=0.0,
                iterations=0,
                applied_rules=[],
                detected_issues=["⚠️ No JSON structure detected in input"]
            )

        self._execute_repair_loop(context)

        self._debug_log(f"After repair loop: {len(context.tokens)} tokens")

        final_json = self.finalizer.process(context)
        self._debug_log(f"Finalized JSON: {final_json}")

        success, python_obj = self._attempt_parse(final_json, context)

        if not success:
            self._debug_log("Parse failed, applying fallback logic")
            success, python_obj, final_json = self._apply_fallback_if_needed(context, success, python_obj, final_json)

        self._finalize_report(context, success, python_obj, final_json)

        return context.report

    def _execute_repair_loop(self, context: Context):
        while context.current_iteration < context.max_iterations:
            context.current_iteration += 1
            any_changed = False

            self._debug_log(f"Iteration {context.current_iteration}")

            if self.bootstrap_flow.execute(context):
                any_changed = True
                self._debug_log(f"Bootstrap changed tokens: {len(context.tokens)}")

            for flow in self.user_flows:
                if flow.execute(context):
                    any_changed = True
                    self._debug_log(f"Flow {flow.__class__.__name__} changed tokens")

            if not any_changed:
                self._debug_log(f"Converged at iteration {context.current_iteration}")
                break

    @staticmethod
    def _attempt_parse(json_text: str, context: Context) -> tuple[bool, Any]:
        try:
            obj = json.loads(json_text)
            return True, obj
        except json.JSONDecodeError as e:
            print(f"[FALLA] JSONDecodeError al intentar parsear: {repr(json_text)}")
            context.report.errors.append(str(e))
            return False, None

    def _apply_fallback_if_needed(self, context: Context, success: bool, python_obj: Any, final_json: str):
        if success:
            return success, python_obj, final_json

        self._debug_log(f"Parse failed. Input: '{final_json}'")

        is_structurally_incomplete = False
        if re.search(r'\{\s*$', final_json.strip()) or re.search(r'\}\s*\.\.\.', final_json):
            is_structurally_incomplete = True

        if is_structurally_incomplete:
            self._debug_log("Detected incomplete JSON, attempting to fix...")
            try:
                try:
                    json.loads(final_json + "}")
                    final_json = final_json + "}"
                    success = True
                    python_obj = json.loads(final_json)
                    self._debug_log(f"Fixed incomplete JSON: {final_json}")
                except:
                    final_json = "{}"
                    python_obj = {}
                    success = False
            except Exception:
                final_json = "{}"
                python_obj = {}
                success = False
        else:
            pass

        if self.mode == "strict":
            if not success:
                self._debug_log("Strict mode enabled, raising exception")
                error_msg = context.report.errors[-1] if context.report.errors else "Unknown unrecoverable error"
                msg = f"PyParseJson (Strict Mode) failed to repair input: {error_msg}"
                doc_preview = final_json[:200] if len(final_json) > 200 else final_json
                raise json.JSONDecodeError(msg=msg, doc=doc_preview, pos=0)

        if not success:
            self._debug_log("Lax mode enabled, returning empty object")
            context.report.detected_issues.append(
                "⚠️ No se pudo reparar el JSON - estructura irrecuperable o incompleta"
            )
            success = True
            python_obj = {}
            final_json = "{}"

        return success, python_obj, final_json

    def _finalize_report(self, context: Context, success: bool, python_obj: Any, final_json: str):
        if not success:
            self._debug_log("Forzando {} en modo lax debido a error de parseo.")
            python_obj = {}
            final_json = "{}"
            context.report.python_object = python_obj
            context.report.json_text = final_json
            context.report.success = True
            context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
            context.report.detected_issues.append("⚠️ Fallback: Forzado '{}' debido a JSON incompleto inválido.")
            return

        quality_score, issues = self.quality_evaluator.evaluate(context)

        context.report.success = success
        context.report.quality_score = quality_score
        context.report.detected_issues.extend(issues)
        context.report.json_text = final_json
        context.report.python_object = python_obj
        context.report.iterations = context.current_iteration

        if success:
            if python_obj == {}:
                if not context.report.applied_rules:
                     context.report.status = RepairStatus.SUCCESS_STRICT_JSON
                else:
                    context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
                    if "No JSON structure detected" not in str(context.report.detected_issues):
                        context.report.detected_issues.append("Returned empty object after repair")
            elif quality_score < 1.0:
                context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
            else:
                context.report.status = RepairStatus.SUCCESS_STRICT_JSON
        else:
            if context.report.applied_rules:
                context.report.status = RepairStatus.PARTIAL_REPAIR
            else:
                context.report.status = RepairStatus.FAILED_UNRECOVERABLE

    def add_flow(self, flow: Flow):
        if not hasattr(flow, "engine") or flow.engine is None:
            flow.engine = self.engine
        self.user_flows.append(flow)

    def parse(self, text: str, dry_run: Optional[bool] = None) -> RepairReport:
        """
        Ejecuta el proceso de reparación sobre un texto.

        Args:
            text: El texto a reparar.
            dry_run: Sobrescribe la configuración de dry_run de la instancia si no es None.

        Returns:
            Un objeto RepairReport con los resultados.

        Raises:
            json.JSONDecodeError: Si mode="strict" y la reparación falla.
        """
        effective_dry_run = self.dry_run if dry_run is None else dry_run
        return self._run(text, dry_run=effective_dry_run)
