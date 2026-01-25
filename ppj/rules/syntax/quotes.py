import re
from ppj.rules.base import Rule

class AddQuotesToKeysRule(Rule):
    """
    Agrega comillas a las claves que no las tienen.
    Ejemplo: { key: "value" } -> { "key": "value" }
    """
    priority = 20
    name = "AddQuotesToKeys"

    def applies(self, context) -> bool:
        # Detecta patrones clave: valor donde clave no tiene comillas
        return bool(re.search(r'(?<!")\b[a-zA-Z_][a-zA-Z0-9_]*\s*:', context.current_text))

    def apply(self, context):
        # Reemplaza palabra: por "palabra":
        # (?<!") asegura que no haya comillas antes
        # \b asegura inicio de palabra
        # ([a-zA-Z_][a-zA-Z0-9_]*) captura la clave
        # \s*: busca el separador
        
        new_text = re.sub(r'(?<!")\b([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'"\1":', context.current_text)
        
        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)
