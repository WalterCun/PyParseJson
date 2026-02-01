# Size: 14.44 KB, Lines: 311

# Path: pyparsejson\core\repair.py
"""
ARCHIVO CORREGIDO: pyparsejson/core/repair.py

CAMBIOS PRINCIPALES:
1. ELIMINADO _extract_balanced_structure() - causaba pérdida de tokens
2. Simplificado _run() - confía en las reglas de wrapping
3. Añadido logging detallado para debugging
4. Corregido _apply_fallback_if_needed()
5. AÑADIDO SOPORTE PARA MODOS (Strict/Lax)
6. AÑADIDO IMPRESIÓN DE EMERGENCIA: Imprime el JSON completo si falla el parseo, no solo el trunco.
"""
import json
import logging
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
        # Inyectar el logger al finalizador
        self.logger = RepairLogger("pyparsejson.repair", level=log_level)
        self.finalizer = JSONFinalize(log_level)
        self.quality_evaluator = RepairQualityEvaluator()

        self.dry_run = dry_run
        self.debug = debug
        self.mode = mode

        # Flujo de arranque (SIEMPRE se ejecuta primero)
        self.bootstrap_flow = BootstrapRepairFlow(self.engine)

        self.user_flows: List[Flow] = []
        if auto_flows:
            self.add_flow(StandardJSONRepairFlow(self.engine))

    def _debug_log(self, message: str):
        """Imprime mensajes de debug si está habilitado."""
        if self.debug:
            print(f"[DEBUG] {message}")

    def _run(self, text: str, dry_run: bool = False) -> RepairReport:
        """Lógica interna de ejecución del pipeline."""
        # 1. Pre-normalización
        clean_text = self.pre_normalize.process(text)
        self._debug_log(f"Pre-normalized text: {clean_text[:100]}...")

        # Caso borde: Texto vacío
        if not clean_text:
            return RepairReport(
                success=True,
                status=RepairStatus.SUCCESS_WITH_WARNINGS,
                json_text="{}",
                python_object={}
            )

        # Inicialización del contexto
        context = Context(clean_text)
        context.tokens = self.tokenizer.tokenize(clean_text)
        context.dry_run = dry_run
        context.report.was_dry_run = dry_run

        self._debug_log(
            f"Initial tokens ({len(context.tokens)}): {[f'{t.type.name}:{t.value}' for t in context.tokens[:10]]}")

        # === DETECCIÓN DE CASOS SIN ESTRUCTURA ===
        # Si no hay tokens de estructura ni pares clave:valor, retornar {} inmediatamente
        has_structure = any(t.type in (TokenType.LBRACE, TokenType.LBRACKET, TokenType.COLON, TokenType.ASSIGN)
                            for t in context.tokens)

        if not has_structure:
            self._debug_log("No structure detected, returning empty object")
            return RepairReport(
                success=True,
                status=RepairStatus.SUCCESS_STRICT_JSON,
                json_text="{}",
                python_object={},
                detected_issues=["⚠️ No JSON structure detected in input"]
            )

        # 2. Bucle de reparación iterativo
        self._execute_repair_loop(context)

        self._debug_log(f"After repair loop: {len(context.tokens)} tokens")

        # 3. Finalización y parseo JSON real
        final_json = self.finalizer.process(context)

        # DEBUG: Imprimir exactamente qué se va a intentar parsear
        self._debug_log(f"Finalized JSON: {final_json}")

        success, python_obj = self._attempt_parse(final_json, context)

        # 4. Fallback final (manejo de modos)
        if not success:
            self._debug_log("Parse failed, applying fallback logic")
            success, python_obj, final_json = self._apply_fallback_if_needed(context, success, python_obj, final_json)

        # 5. Evaluación de calidad y construcción del reporte
        self._finalize_report(context, success, python_obj, final_json)

        return context.report

    def _execute_repair_loop(self, context: Context):
        """Ejecuta los flujos de reparación hasta que no haya cambios o se alcance el límite."""
        while context.current_iteration < context.max_iterations:
            context.current_iteration += 1
            any_changed = False

            self._debug_log(f"Iteration {context.current_iteration}")

            # Bootstrap flow (siempre primero)
            if self.bootstrap_flow.execute(context):
                any_changed = True
                self._debug_log(f"Bootstrap changed tokens: {len(context.tokens)}")

            # User / standard flows
            for flow in self.user_flows:
                if flow.execute(context):
                    any_changed = True
                    self._debug_log(f"Flow {flow.__class__.__name__} changed tokens")

            # Si no hubo cambios en esta iteración, el sistema es estable
            if not any_changed:
                self._debug_log(f"Converged at iteration {context.current_iteration}")
                break

    @staticmethod
    def _attempt_parse(json_text: str, context: Context) -> tuple[bool, Any]:
        """Intenta parsear el JSON resultante con la librería estándar."""
        try:
            obj = json.loads(json_text)
            return True, obj
        except json.JSONDecodeError as e:
            # IMPRESIÓN DE EMERGENCIA: Imprimir el JSON COMPLETO
            # Esto nos dirá exactamente qué está llegando al parser y por qué falla.
            # El error 'Expecting , delimiter' es muy común.
            print(f"[FALLA] JSONDecodeError al intentar parsear: {repr(json_text)}")
            context.report.errors.append(str(e))
            return False, None

    def _apply_fallback_if_needed(self, context: Context, success: bool, python_obj: Any, final_json: str):
        """
        Manejo de errores finales basado en el modo de operación.

        LAX MODE (Default): Devuelve {} para no romper la aplicación.
        STRICT MODE: Lanza excepción para forzar el manejo del error.
        """
        if success:
            return success, python_obj, final_json

        # El parse falló (success=False). Analizar por qué.
        self._debug_log(f"Parse failed. Input: '{final_json}'")

        # Chequeo de inconsistencia: El parseo falló pero el JSON parece estructurado.
        # Esto suele pasar si el JSON está incompleto (ej: { "a": 1... )
        # Si el JSON parece incompleto, consideramos que es un error fatal.
        # Verificamos si es válido con un parser más estricto o regex simple.
        is_structurally_incomplete = False

        # Comprobación simple de JSON incompleto usando regex (más rápido que json.loads)
        # Busca patrones como "{" (no hay cierre) o }... (exceso de cierre)
        import re
        # Un JSON inválido común es que termina con "..."
        if re.search(r'\{\s*$', final_json.strip()) or re.search(r'\}\s*\.\.\.', final_json):
            is_structurally_incomplete = True

        # Si parece incompleto, no intentar arreglar, solo retornar {}.
        # Intentar arreglar un cierre faltante (ej: añadir '}')
        if is_structurally_incomplete:
            # Intentar arreglar añadiendo } al final
            self._debug_log("Detected incomplete JSON, attempting to fix...")
            try:
                # Estrategia simple: Añadir '}' al final.
                # Si sigue fallando, limpiar a '{}'.
                try:
                    # Intentar parsear el JSON limpio
                    json.loads(final_json + "}")
                    # Si llega aquí, es que el JSON principal era válido, solo le faltaba el cierre.
                    final_json = final_json + "}"
                    success = True
                    python_obj = json.loads(final_json)
                    self._debug_log(f"Fixed incomplete JSON: {final_json}")
                except:
                    # Si falla el parseo, limpiar a {}.
                    final_json = "{}"
                    python_obj = {}
                    success = False
            except Exception:
                final_json = "{}"
                python_obj = {}
                success = False
        else:
            # No parece incompleto, quizás error de sintaxis grave.
            # No podemos hacer mucho más sin arriesgar el JSON.
            pass

        # Lógica de modos
        if self.mode == "strict":
            # En modo estricto, fallar explícitamente es mejor que devolver datos vacíos o vacíos.
            if not success:
                self._debug_log("Strict mode enabled, raising exception")
                error_msg = context.report.errors[-1] if context.report.errors else "Unknown unrecoverable error"
                # Usar el JSON generado (que podría estar incompleto) para el mensaje de error
                msg = f"PyParseJson (Strict Mode) failed to repair input: {error_msg}"
                # Si el final_json es muy largo, truncarlo para el mensaje
                doc_preview = final_json[:200] if len(final_json) > 200 else final_json

                raise json.JSONDecodeError(msg=msg, doc=doc_preview, pos=0)

        if not success:
            # Modo Lax (Default): Comportamiento original
            self._debug_log("Lax mode enabled, returning empty object")
            context.report.detected_issues.append(
                "⚠️ No se pudo reparar el JSON - estructura irrecuperable o incompleta"
            )
            success = True
            python_obj = {}
            final_json = "{}"

        return success, python_obj, final_json

    def _finalize_report(self, context: Context, success: bool, python_obj: Any, final_json: str):
        # CORRECCIÓN: Paréntesis de cierre movidos a nueva línea
        if not success:
            # Si la reparación falló y estamos en modo lax (por defecto), es probable que final_json esté incompleto (ej: `{"a": 1...`).
            # Se fuerza un retorno seguro de "{}".
            self._debug_log("Forzando {} en modo lax debido a error de parseo.")
            python_obj = {}
            final_json = "{}"
            # Actualizar el reporte para reflejar este estado.
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

        # Determinar estado final detallado
        if success:
            if python_obj == {}:
                context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
                if "No JSON structure detected" not in str(context.report.detected_issues):
                    context.report.detected_issues.append("Returned empty object after repair failure")
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
        """Agrega un flujo de reparación personalizado al pipeline."""
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
