import re
from ppj.rules.base import Rule

class NormalizeBooleansRule(Rule):
    """
    Normaliza booleanos y null (si/no, True/False -> true/false, null).
    """
    priority = 50
    name = "NormalizeBooleans"

    def applies(self, context) -> bool:
        text = context.current_text.lower()
        keywords = ["true", "false", "null", "none", "si", "no"]
        return any(k in text for k in keywords)

    def apply(self, context):
        new_text = context.current_text
        
        map_vals = {
            'True': 'true', 'False': 'false', 'None': 'null',
            'si': 'true', 'no': 'false',
            'yes': 'true'
        }
        
        for wrong, right in map_vals.items():
            # Regex: (?<=[:\[,])\s*wrong\b
            pattern = re.compile(r'(?<=[:\[,])\s*' + re.escape(wrong) + r'\b', re.IGNORECASE)
            new_text = pattern.sub(right, new_text)
            
            # Caso inicio string
            if re.match(r'^\s*' + re.escape(wrong) + r'\b', new_text, re.IGNORECASE):
                 new_text = re.sub(r'^\s*' + re.escape(wrong) + r'\b', right, new_text, count=1, flags=re.IGNORECASE)

        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)

class QuoteUnquotedValuesRule(Rule):
    """
    Intenta poner comillas a valores que parecen strings pero no las tienen.
    Ejemplo: "date": 2022-01-01 -> "date": "2022-01-01"
    """
    priority = 60
    name = "QuoteUnquotedValues"
    
    def applies(self, context) -> bool:
        # Heurística: : valor
        # Donde valor no es true, false, null, numero, {, [ o "string"
        return True

    def apply(self, context):
        # Regex compleja para identificar valores no válidos en JSON
        # Buscamos: : \s* (algo que no empieza con ", digit, t, f, n, {, [)
        # Y que termina en , } ] o fin de linea
        
        # Grupo 1: separador previo (: o , o [)
        # Grupo 2: el valor sospechoso
        # Lookahead: terminador
        
        # Excluir:
        # - Numeros (incluyendo negativos y decimales)
        # - true, false, null
        # - Strings con comillas
        # - Objetos y listas
        
        # Patrón de valor válido (simplificado):
        # \".*?\" | [-]?\d+(\.\d+)?([eE][+-]?\d+)? | true | false | null | \{ | \[
        
        # Patrón de valor inválido:
        # [^"0-9\-\[\{tfn\s][^,}\]]*
        # Empieza con algo que no es comilla, digito, -, [, {, t, f, n (cuidado con true/false/null mal escritos o parciales)
        # Pero t, f, n pueden ser inicio de texto normal "title".
        
        # Mejor enfoque: Iterar sobre pares clave:valor y verificar valor.
        # Regex: "key"\s*:\s*([^,}\]]+)
        
        def replace_val(match):
            val = match.group(1).strip()
            if not val: return match.group(0)
            
            # Si ya es válido, dejarlo
            if val.startswith('"') and val.endswith('"'): return match.group(0)
            if val.startswith('{') or val.startswith('['): return match.group(0)
            if val in ['true', 'false', 'null']: return match.group(0)
            if re.match(r'^-?\d+(\.\d+)?([eE][+-]?\d+)?$', val): return match.group(0)
            
            # Si no es válido, poner comillas
            return match.group(0).replace(val, f'"{val}"')

        # Aplicar a valores después de :
        new_text = re.sub(r'(?<=:)\s*([^,}\]]+)', replace_val, context.current_text)

        if new_text != context.current_text:
            context.current_text = new_text
            context.record_rule(self.name)
