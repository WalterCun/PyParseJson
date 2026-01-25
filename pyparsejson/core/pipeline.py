import json
from pyparsejson.core.context import Context
from pyparsejson.phases.pre_normalize import PreNormalizeText
from pyparsejson.phases.tokenize import TolerantTokenizer
from pyparsejson.phases.structure_repair import StructureRepair
from pyparsejson.phases.value_normalize import ValueNormalize
from pyparsejson.phases.json_finalize import JSONFinalize
from pyparsejson.report.repair_report import RepairReport

class Pipeline:
    def __init__(self):
        self.pre_normalize = PreNormalizeText()
        self.tokenizer = TolerantTokenizer()
        self.structure_repair = StructureRepair()
        self.value_normalize = ValueNormalize()
        self.finalizer = JSONFinalize()

    def parse(self, text: str) -> RepairReport:
        # 1. Pre-normalización
        clean_text = self.pre_normalize.process(text)
        context = Context(clean_text)
        
        # 2. Tokenización inicial
        context.tokens = self.tokenizer.tokenize(clean_text)
        
        # Ciclo de reparación
        success = False
        final_json = ""
        python_obj = None
        
        while context.current_iteration < context.max_iterations:
            context.current_iteration += 1
            context.changed_in_last_pass = False
            
            # 3. Reparación Estructural
            self.structure_repair.process(context)
            
            # 4. Normalización de Valores
            self.value_normalize.process(context)
            
            # 5. Finalización (Generación de JSON candidato)
            final_json = self.finalizer.process(context)
            
            # 6. Validación
            try:
                python_obj = json.loads(final_json)
                success = True
                break # ¡Éxito!
            except json.JSONDecodeError:
                # Si falló, y hubo cambios, intentamos otra vuelta.
                # Si no hubo cambios, no podemos hacer más nada con las reglas actuales.
                if not context.changed_in_last_pass:
                    break
        
        # Construir reporte
        context.report.success = success
        context.report.json_text = final_json if success else None # O devolver el best-effort
        context.report.python_object = python_obj
        context.report.iterations = context.current_iteration
        
        if not success:
            context.report.json_text = final_json # Devolver el intento fallido para debug
            context.report.errors.append("Could not generate valid JSON after max iterations.")

        return context.report
