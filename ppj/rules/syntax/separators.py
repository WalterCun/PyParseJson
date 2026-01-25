import re
from ppj.rules.base import Rule

class EqualToColonRule(Rule):
    """
    Convierte asignaciones con '=' a formato JSON con ':'.
    Ejemplo: "key=value" -> "key:value"
    """
    priority = 10
    name = "EqualToColon"

    def applies(self, context) -> bool:
        # Busca patrones tipo palabra=valor donde no esté entre comillas
        # Esta es una heurística simple.
        return "=" in context.current_text

    def apply(self, context):
        # Reemplaza = por : cuando parece ser un separador de campo
        # Evitamos reemplazar dentro de strings si es posible, pero
        # en esta fase de reparación asumiendo input roto, un replace global
        # o regex simple suele ser el primer paso.
        
        # Regex: (palabra o string) \s* = \s* (valor)
        # Simplificación: reemplazar = por : si no está rodeado de comillas claras
        # O simplemente reemplazar todos los = que no parezcan estar en un string.
        
        # Para esta implementación inicial, usaremos una regex que busca
        # identificadores seguidos de =
        
        # Patrón: (palabra alfanumérica) \s* =
        new_text = re.sub(r'([a-zA-Z0-9_]+)\s*=', r'\1:', context.current_text)
        
        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)
