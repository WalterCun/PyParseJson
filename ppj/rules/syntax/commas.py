import re
from ppj.rules.base import Rule

class RemoveTrailingCommasRule(Rule):
    """
    Elimina comas al final de objetos o listas.
    Ejemplo: { "a": 1, } -> { "a": 1 }
    """
    priority = 30
    name = "RemoveTrailingCommas"

    def applies(self, context) -> bool:
        return ",}" in context.current_text or ",]" in context.current_text or ", }" in context.current_text or ", ]" in context.current_text

    def apply(self, context):
        new_text = re.sub(r',\s*([}\]])', r'\1', context.current_text)
        
        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)

class AddMissingCommasRule(Rule):
    """
    Agrega comas faltantes entre pares clave-valor si están separados por espacios o saltos de línea.
    Ejemplo: {"a":1 "b":2} -> {"a":1, "b":2}
    """
    priority = 35
    name = "AddMissingCommas"
    
    def applies(self, context) -> bool:
        # Heurística: busca "valor" "clave": o numero "clave":
        # Esto es complejo con regex simple, pero intentaremos cubrir casos comunes
        return True # Intentar aplicar siempre que sea seguro

    def apply(self, context):
        # Caso: "valor" "clave" -> "valor", "clave"
        # Caso: 123 "clave" -> 123, "clave"
        # Caso: true "clave" -> true, "clave"
        
        # Patrón general: (valor_terminado)\s+(?="[\w]+":)
        # Valores terminados: "string", numero, true, false, null, }, ]
        
        # Regex para insertar coma entre un valor y una clave siguiente
        # Grupo 1: fin de valor (comilla, digito, e, l, }, ])
        # Grupo 2: espacio
        # Lookahead: siguiente clave
        
        # Simplificación: buscar cierre de comillas o digito seguido de espacio y luego apertura de comillas de clave
        
        # "value" "key":
        new_text = re.sub(r'("\s*|\d\s*|true\s*|false\s*|null\s*|[}\]]\s*)(?="[a-zA-Z0-9_]+":)', r'\1,', context.current_text)
        
        # Limpieza de dobles comas si se generaron
        new_text = new_text.replace(",,", ",")
        
        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)
