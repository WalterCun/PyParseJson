from typing import List
from pyparsejson.core.context import Context
from pyparsejson.rules.structure.separators import EqualToColonRule, AddMissingCommasRule, TupleToListRule
from pyparsejson.rules.structure.wrappers import WrapLoosePairsRule

class StructureRepair:
    """
    Fase de reparación estructural: arregla separadores, listas, objetos.
    """
    def __init__(self):
        self.rules = [
            WrapLoosePairsRule(),
            TupleToListRule(),
            EqualToColonRule(),
            AddMissingCommasRule(),
        ]
        self.rules.sort(key=lambda r: r.priority)

    def process(self, context: Context):
        for rule in self.rules:
            if rule.applies(context):
                rule.apply(context)
