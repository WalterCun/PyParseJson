from ppj.rules.base import Rule

class CloseBracketsRule(Rule):
    """
    Cierra llaves y corchetes abiertos que faltan al final.
    """
    priority = 90
    name = "CloseBrackets"

    def applies(self, context) -> bool:
        open_braces = context.current_text.count('{')
        close_braces = context.current_text.count('}')
        open_brackets = context.current_text.count('[')
        close_brackets = context.current_text.count(']')
        return open_braces > close_braces or open_brackets > close_brackets

    def apply(self, context):
        # Estrategia simple: contar y cerrar en orden inverso de aparición (stack)
        # O simplemente agregar al final lo que falta.
        # Para JSON simple, agregar al final suele funcionar si la estructura no está anidada complejamente de forma incorrecta.
        
        # Un enfoque más robusto sería rastrear el último abierto.
        # Aquí usaremos un enfoque de stack simple para determinar qué cerrar.
        
        stack = []
        for char in context.current_text:
            if char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}' or char == ']':
                if stack and stack[-1] == char:
                    stack.pop()
        
        # Lo que queda en stack es lo que falta cerrar, en orden inverso (porque stack tiene lo que esperamos encontrar)
        # Pero stack se llenó en orden de apertura. Si tenemos { [, stack es ['}', ']'].
        # Debemos cerrar primero el último abierto: ] y luego }.
        # Así que debemos agregar stack.reverse() al texto.
        
        if stack:
            closing_chars = "".join(reversed(stack))
            context.current_text += closing_chars
            context.record_rule(self.name)

class WrapLoosePairsRule(Rule):
    """
    Envuelve pares clave/valor sueltos en un objeto JSON si no lo están.
    Ejemplo: "a": 1 -> {"a": 1}
    """
    priority = 95
    name = "WrapLoosePairs"

    def applies(self, context) -> bool:
        text = context.current_text.strip()
        if not text:
            return False
        # Si no empieza con { o [
        return not (text.startswith('{') or text.startswith('['))

    def apply(self, context):
        context.current_text = "{" + context.current_text + "}"
        context.record_rule(self.name)

class TupleToListRule(Rule):
    """
    Convierte tuplas (1,2,3) a listas [1,2,3].
    """
    priority = 40
    name = "TupleToList"

    def applies(self, context) -> bool:
        return "(" in context.current_text and ")" in context.current_text

    def apply(self, context):
        # Reemplaza ( por [ y ) por ]
        # Cuidado con texto dentro de strings, pero asumimos reparación agresiva.
        # Mejor: reemplazar ( al inicio de estructura o después de : o ,
        
        # Enfoque simple: reemplazar todos los () que parezcan estructura
        # (no dentro de comillas idealmente, pero aquí haremos replace simple por ahora
        # o un translate)
        
        # Para ser un poco más seguros, iteramos y reemplazamos si no estamos en string.
        # Implementación simplificada: replace directo.
        
        new_text = context.current_text.replace('(', '[').replace(')', ']')
        
        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)
