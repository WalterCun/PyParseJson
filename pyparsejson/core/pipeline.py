import json
from typing import List
from pyparsejson.core.context import Context
from pyparsejson.core.engine import RuleEngine
from pyparsejson.core.flow import Flow, PreRepairFlow, ValueNormalizationFlow, FinalizationFlow
from pyparsejson.phases.pre_normalize import PreNormalizeText
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.phases.json_finalize import JSONFinalize
from pyparsejson.models.repair_report import Report

class Pipeline:
    def __init__(self):
        self.engine = RuleEngine()
        self.flows: List[Flow] = []
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.finalizer = JSONFinalize()
        
        # Configuración por defecto
        self.add_flow(PreRepairFlow(self.engine))
        self.add_flow(ValueNormalizationFlow(self.engine))
        self.add_flow(FinalizationFlow(self.engine))

    def add_flow(self, flow: Flow):
        self.flows.append(flow)

    def parse(self, text: str) -> Report:
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
                context.report.errors.append(str(e))
                if not context.changed_in_last_pass:
                    break
        
        # Construir reporte
        context.report.success = success
        context.report.json_text = final_json
        context.report.python_object = python_obj
        context.report.iterations = context.current_iteration
        
        return context.report
