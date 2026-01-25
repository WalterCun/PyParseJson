from pyparsejson.core.context import Context
from pyparsejson.rules.values.literals import NormalizeBooleansRule, QuoteBareWordsRule

class ValueNormalize:
    """
    Fase de normalización de valores: tipos de datos, formatos.
    """
    def __init__(self):
        self.rules = [
            NormalizeBooleansRule(),
            QuoteBareWordsRule(),
            # Aquí irían reglas de fechas, números, etc.
        ]
        self.rules.sort(key=lambda r: r.priority)

    def process(self, context: Context):
        for rule in self.rules:
            if rule.applies(context):
                rule.apply(context)
