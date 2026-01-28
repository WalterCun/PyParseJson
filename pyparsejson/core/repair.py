import json
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


class Repair:
    """
    Orquestador principal del proceso de reparación de JSON.
    Coordina las fases de normalización, tokenización, aplicación de reglas y finalización.
    """

    # -------------------------------- #
    #            CONSTRUCTOR           #
    # -------------------------------- #

    def __init__(self, auto_flows: bool = True, dry_run: bool = False):
        """
        Inicializa el motor de reparación.

        Args:
            auto_flows: Si es True, carga los flujos de reparación estándar.
            dry_run: Si es True, ejecuta en modo auditoría sin aplicar cambios finales.
        """
        self.engine = RuleEngine()
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.finalizer = JSONFinalize()
        self.quality_evaluator = RepairQualityEvaluator()

        self.dry_run = dry_run

        # Flujo de arranque (SIEMPRE se ejecuta primero para garantizar estructura básica)
        self.bootstrap_flow = BootstrapRepairFlow(self.engine)

        self.user_flows: List[Flow] = []
        if auto_flows:
            self.add_flow(StandardJSONRepairFlow(self.engine))

    # -------------------------------- #
    #        METODOS PRIVADOS          #
    # -------------------------------- #

    def _run(self, text: str, dry_run: bool = False) -> RepairReport:
        """Lógica interna de ejecución del pipeline."""
        # 1. Pre-normalización
        clean_text = self.pre_normalize.process(text)

        # Caso borde: Texto vacío
        if not clean_text:
            return RepairReport(
                success=True,
                status=RepairStatus.SUCCESS_STRICT_JSON,
                json_text="{}",
                python_object={}
            )

        # Inicialización del contexto
        context = Context(clean_text)
        context.tokens = self.tokenizer.tokenize(clean_text)
        context.dry_run = dry_run
        context.report.was_dry_run = dry_run

        # 2. Bucle de reparación iterativo
        self._execute_repair_loop(context)

        # 3. Finalización y parseo JSON real
        final_json = self.finalizer.process(context)
        success, python_obj = self._attempt_parse(final_json, context)

        # 4. Fallback de emergencia para basura no estructurada
        if not success:
            success, python_obj, final_json = self._apply_fallback_if_needed(context, success, python_obj,
                                                                             final_json)

        # 5. Evaluación de calidad y construcción del reporte
        self._finalize_report(context, success, python_obj, final_json)

        return context.report

    def _execute_repair_loop(self, context: Context):
        """Ejecuta los flujos de reparación hasta que no haya cambios o se alcance el límite."""
        while context.current_iteration < context.max_iterations:
            context.current_iteration += 1
            any_changed = False

            # Bootstrap flow (siempre primero)
            if self.bootstrap_flow.execute(context):
                any_changed = True

            # User / standard flows
            for flow in self.user_flows:
                if flow.execute(context):
                    any_changed = True

            # Si no hubo cambios en esta iteración, el sistema es estable
            if not any_changed:
                break

    @staticmethod
    def _attempt_parse(json_text: str, context: Context) -> tuple[bool, Any]:
        """Intenta parsear el JSON resultante con la librería estándar."""
        try:
            obj = json.loads(json_text)
            return True, obj
        except json.JSONDecodeError as e:
            context.report.errors.append(str(e))
            return False, None

    def _apply_fallback_if_needed(self, context: Context, success: bool, python_obj: Any, final_json: str):
        """
        Maneja inputs sin estructura JSON raíz detectable.
        - Si hay tokens pero sin estructura raíz: intenta extraer objetos/array anidados
        - Si no hay tokens ni estructura detectable: NO marca como éxito (evita falsos positivos)
        """
        # Caso 1: Ya tenemos éxito → no intervenir
        if success:
            return success, python_obj, final_json

        # Caso 2: Tokens existen pero sin estructura raíz → intentar extraer objetos/array anidados
        if context.tokens and context.tokens[0].type not in (TokenType.LBRACE, TokenType.LBRACKET):
            extracted = self._extract_balanced_structure(context.tokens)
            if extracted:
                # EXTRAER la estructura y CONTINUAR el ciclo de reparación (no detenerse)
                context.tokens = extracted
                context.mark_changed()
                context.report.detected_issues.append(
                    f"Estructura raíz extraída desde texto mixto (longitud: {len(extracted)} tokens)"
                )
                # ⚠️ IMPORTANTE: Devolver False para que el motor continúe reparando
                return False, None, ""  # El "" fuerza re-parseo en siguiente iteración

            # Si no hay estructura anidada detectable → texto plano sin JSON
            context.report.detected_issues.append(
                "⚠️ ADVERTENCIA: Texto sin estructura JSON detectable. No se puede reparar."
            )
            return False, None, "{}"  # Mantener estado de fallo

        # Caso 3: Tokens con estructura raíz pero parseo fallido → ya se maneja en _attempt_parse
        return success, python_obj, final_json

    @staticmethod
    def _extract_balanced_structure(tokens: List[Token]) -> Optional[List[Token]]:
        """
        Extrae la PRIMERA estructura balanceada (objeto/array) encontrada en la lista de tokens.
        Ej: "hola {a:1, b:2} mundo" → extrae "{a:1, b:2}"
        """
        if not tokens:
            return None

        # Buscar primera apertura de estructura
        start_idx = -1
        start_type = None
        for i, token in enumerate(tokens):
            if token.type in (TokenType.LBRACE, TokenType.LBRACKET):
                start_idx = i
                start_type = token.type
                break

        if start_idx == -1:
            return None  # No hay estructura anidada

        # Balancear hasta encontrar el cierre correspondiente
        close_type = TokenType.RBRACE if start_type == TokenType.LBRACE else TokenType.RBRACKET
        depth = 0
        end_idx = -1

        for i in range(start_idx, len(tokens)):
            t = tokens[i]
            if t.type == start_type:
                depth += 1
            elif t.type == close_type:
                depth -= 1
                if depth == 0:
                    end_idx = i
                    break

        if end_idx != -1:
            return tokens[start_idx:end_idx + 1]
        return None

    def _finalize_report(self, context: Context, success: bool, python_obj: Any, final_json: str):
        """Calcula métricas de calidad y rellena el reporte final."""
        quality_score, issues = self.quality_evaluator.evaluate(context)

        context.report.success = success
        context.report.quality_score = quality_score
        context.report.detected_issues.extend(issues)
        context.report.json_text = final_json
        context.report.python_object = python_obj
        context.report.iterations = context.current_iteration

        # Determinar estado final detallado
        if success:
            if quality_score < 1.0 or (python_obj == {} and "Devuelve {}" in str(context.report.detected_issues)):
                context.report.status = RepairStatus.SUCCESS_WITH_WARNINGS
            else:
                context.report.status = RepairStatus.SUCCESS_STRICT_JSON
        else:
            if context.report.applied_rules:
                context.report.status = RepairStatus.PARTIAL_REPAIR
            else:
                context.report.status = RepairStatus.FAILED_UNRECOVERABLE

    # -------------------------------- #
    #         METODOS PUBLICOS         #
    # -------------------------------- #

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
        """
        effective_dry_run = self.dry_run if dry_run is None else dry_run
        return self._run(text, dry_run=effective_dry_run)
