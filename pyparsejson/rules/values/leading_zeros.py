import re
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


@RuleRegistry.register(tags=["values", "normalization"], priority=45)
class LeadingZeroIdentifierRule(Rule):
    """
    Detecta tokens numéricos que comienzan con '0' (pero no son '0', ni decimales, ni notación científica)
    y los convierte a STRING para preservar su valor semántico (ej: códigos postales, identificadores).
    
    Ejemplo: 0123 -> "0123"
    """

    def applies(self, context: Context) -> bool:
        for token in context.tokens:
            if token.type == TokenType.NUMBER:
                val = token.value
                # Condición rápida: empieza con 0 y tiene más de 1 caracter
                if len(val) > 1 and val.startswith('0'):
                    # Validaciones más costosas solo si pasa el filtro inicial
                    if not val.startswith('0.') and 'e' not in val.lower():
                        return True
        return False

    def apply(self, context: Context):
        changed = False
        
        for token in context.tokens:
            if token.type == TokenType.NUMBER:
                val = token.value
                
                # Regla:
                # 1. len > 1
                # 2. startswith("0")
                # 3. NOT startswith("0.")
                # 4. NOT contains "e" or "E" (notación científica)
                
                if (len(val) > 1 and 
                    val.startswith('0') and 
                    not val.startswith('0.') and 
                    'e' not in val.lower()):
                    
                    # Convertir a STRING
                    token.type = TokenType.STRING
                    token.value = f'"{val}"'
                    token.raw_value = token.value
                    
                    # Registrar warning interno
                    context.report.detected_issues.append(f"leading_zero_numeric_identifier: {val}")
                    
                    changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)
