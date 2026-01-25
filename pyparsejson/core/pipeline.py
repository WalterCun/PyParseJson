import json
from typing import List
from pyparsejson.core.context import Context
from pyparsejson.core.engine import RuleEngine
from pyparsejson.core.flow import Flow, PreRepairFlow, ValueNormalizationFlow, FinalizationFlow
from pyparsejson.phases.pre_normalize import PreNormalizeText
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.phases.json_finalize import JSONFinalize
from pyparsejson.report.repair_report import RepairReport, RepairStatus
from pyparsejson.core.quality import RepairQualityEvaluator

class Pipeline:
    def __init__(self):
        self.engine = RuleEngine()
        self.flows: List[Flow] = []
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.finalizer = JSONFinalize()
        self.quality_evaluator = RepairQualityEvaluator()
        
        # Configuración por defecto
        self.add_flow(PreRepairFlow(self.engine))
        self.add_flow(ValueNormalizationFlow(self.engine))
        self.add_flow(FinalizationFlow(self.engine))

    def add_flow(self, flow: Flow):
        self.flows.append(flow)

    def parse(self, text: str) -> RepairReport:
        # 1. Pre-procesamiento
        clean_text = self.pre_normalize.process(text)
        context = Context(clean_text)
        context.tokens = self.tokenizer.tokenize(clean_text)
        
        success = False
        final_json = ""
        python_obj = None
        
        # Ciclo de reparación automática
        while context.current_iteration < context.max_iterations:
            context.current_iteration += 1
            context.changed_in_last_pass = False
            
            # Ejecutar flujos configurados
            for flow in self.flows:
                flow.execute(context)
            
            # Generar JSON candidato
            final_json = self.finalizer.process(context)
            
            # Validar
            try:
                python_obj = json.loads(final_json)
                success = True
                break
            except json.JSONDecodeError as e:
                # Solo registrar el error si es la última iteración o si no hubo cambios
                if context.current_iteration == context.max_iterations or not context.changed_in_last_pass:
                    context.report.errors.append(str(e))
                
                if not context.changed_in_last_pass:
                    break
        
        # Evaluación Final de Calidad
        quality_score, issues = self.quality_evaluator.evaluate(context)
        context.report.quality_score = quality_score
        context.report.detected_issues = issues
        
        # Cálculo de Confianza
        context.report.confidence = self._calculate_confidence(success, quality_score, context)
        
        # Determinación de Estado
        if success:
            context.report.status = RepairStatus.SUCCESS_STRICT_JSON
            context.report.success = True
        elif quality_score > 0.6: # Umbral arbitrario para "parcialmente útil"
            context.report.status = RepairStatus.PARTIAL_REPAIR
            context.report.success = False
        else:
            context.report.status = RepairStatus.FAILED_UNRECOVERABLE
            context.report.success = False

        context.report.json_text = final_json
        context.report.python_object = python_obj
        context.report.iterations = context.current_iteration
        
        return context.report

    def _calculate_confidence(self, success: bool, quality: float, context: Context) -> float:
        """
        Calcula un score de confianza basado en éxito, calidad e iteraciones.
        """
        base_confidence = quality
        
        if success:
            # Si parseó, la confianza es alta, pero penalizada por cuántas vueltas dio
            iteration_penalty = (context.current_iteration - 1) * 0.05
            return min(1.0, max(0.5, 1.0 - iteration_penalty))
        
        # Si no parseó, la confianza depende puramente de la calidad estructural
        # y se penaliza severamente
        return round(base_confidence * 0.5, 2)
