import json
from typing import List

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


class Pipeline:
    """
    Orquestador principal del proceso de reparación de JSON.
    """

    def __init__(self, auto_flows: bool = True):
        self.engine = RuleEngine()
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.finalizer = JSONFinalize()
        self.quality_evaluator = RepairQualityEvaluator()

        # Flujo de arranque (SIEMPRE se ejecuta primero)
        self.bootstrap_flow = BootstrapRepairFlow(self.engine)

        self.user_flows: List[Flow] = []
        if auto_flows:
            self.add_flow(StandardJSONRepairFlow(self.engine))

    def add_flow(self, flow: Flow):
        if not hasattr(flow, "engine") or flow.engine is None:
            flow.engine = self.engine
        self.user_flows.append(flow)

    def parse(self, text: str) -> RepairReport:
        # 1. Pre-normalización y tokenización
        clean_text = self.pre_normalize.process(text)
        context = Context(clean_text)
        context.tokens = self.tokenizer.tokenize(clean_text)

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

        # 4. Evaluación de calidad (UNA sola vez)
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
            if context.report.applied_rules:
                context.report.status = RepairStatus.PARTIAL_REPAIR
            else:
                context.report.status = RepairStatus.FAILED_UNRECOVERABLE

        return context.report
