from ppj.engine.context import Context
from ppj.rules.syntax.separators import EqualToColonRule
from ppj.rules.syntax.quotes import AddQuotesToKeysRule
from ppj.rules.syntax.commas import RemoveTrailingCommasRule, AddMissingCommasRule
from ppj.rules.syntax.brackets import CloseBracketsRule, WrapLoosePairsRule, TupleToListRule
from ppj.rules.syntax.literals import NormalizeBooleansRule, QuoteUnquotedValuesRule

class RepairStage:
    """
    Etapa de reparación sintáctica del pipeline.
    Intenta transformar texto mal formado en JSON válido.
    """
    
    def __init__(self):
        # Inicializar reglas ordenadas por prioridad
        self.rules = [
            TupleToListRule(),       # 40: (..) -> [..] antes de procesar contenido
            EqualToColonRule(),      # 10: = -> :
            AddQuotesToKeysRule(),   # 20: key: -> "key":
            NormalizeBooleansRule(), # 50: si/no -> true/false
            QuoteUnquotedValuesRule(), # 60: date: 2022-01-01 -> date: "2022-01-01"
            AddMissingCommasRule(),  # 35: "a":1 "b":2 -> "a":1, "b":2
            RemoveTrailingCommasRule(), # 30: ,} -> }
            WrapLoosePairsRule(),    # 95: "a":1 -> {"a":1} (si no hay llaves)
            CloseBracketsRule(),     # 90: {.. -> {..}
        ]
        # Reordenar explícitamente por si acaso
        self.rules.sort(key=lambda r: r.priority)
        
        self.max_iterations = 10

    def process(self, context: Context, schema=None):
        """
        Ejecuta el ciclo de reparación sobre el contexto.
        """
        iteration = 0
        changed = True
        
        while changed and iteration < self.max_iterations:
            changed = False
            iteration += 1
            
            # Guardar estado antes de la pasada
            text_before_pass = context.current_text
            
            for rule in self.rules:
                if rule.applies(context):
                    # Guardar texto antes de la regla para verificar cambios
                    text_before_rule = context.current_text
                    
                    rule.apply(context)
                    
                    if context.current_text != text_before_rule:
                        # Si una regla cambió algo, marcamos para seguir iterando
                        # (algunas reglas pueden habilitar otras)
                        changed = True
            
            # Si en toda la pasada no hubo cambios, terminamos
            if context.current_text == text_before_pass:
                changed = False

        return context
