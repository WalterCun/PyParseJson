"""
ARCHIVO CORREGIDO: pyparsejson/phases/json_finalize.py

CAMBIOS PRINCIPALES:
1. Añadido logging detallado de cada token procesado
2. Corregida lógica de manejo de comillas
3. Añadida validación de tokens vacíos
"""
import logging

from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType
from pyparsejson.utils.logger import RepairLogger


class JSONFinalize:
    """
    Convierte la lista de tokens reparada en un string JSON sintácticamente estricto.
    Esta es la última fase antes de intentar el parseo final con `json.loads`.
    """

    def __init__(self, log_level: int = logging.WARNING):
        self.logger = RepairLogger("JSONFinalize", level=log_level)

    def process(self, context: Context) -> str:
        """
        Convierte tokens a string JSON válido SIN duplicar comillas.
        """
        if not context.tokens:
            print("[FINALIZE] ⚠️ WARNING: No hay tokens para procesar")
            return "{}"
        # print(f"[FINALIZE] Procesando {len(context.tokens)} tokens")

        parts = []
        for i, token in enumerate(context.tokens):
            # DEBUG: Descomentar para ver qué está procesando
            self.logger(f"[FINALIZE] Token {i}: {token.type.name} = '{token.value}'")

            if token.type == TokenType.STRING:
                val = token.value

                # Caso 1: Ya tiene comillas dobles válidas → usar tal cual
                if val.startswith('"') and val.endswith('"') and len(val) >= 2:
                    parts.append(val)
                    continue

                # Caso 2: Comillas simples → convertir a dobles
                if val.startswith("'") and val.endswith("'") and len(val) >= 2:
                    content = val[1:-1].replace('"', '\\"').replace("\\'", "'")
                    parts.append(f'"{content}"')
                    continue

                # Caso 3: Sin comillas → añadir
                # Importante: Escapar comillas internas
                content = val.replace('\\', '\\\\').replace('"', '\\"')
                parts.append(f'"{content}"')

            elif token.type == TokenType.BOOLEAN:
                # Normalizar a lowercase (true/false estándar JSON)
                parts.append(token.value.lower())

            elif token.type == TokenType.NULL:
                parts.append("null")

            elif token.type == TokenType.DATE:
                # Las fechas siempre van como strings
                parts.append(f'"{token.value}"')

            elif token.type == TokenType.NUMBER:
                # Números van sin comillas
                parts.append(token.value)

            else:
                # Estructuras (llaves, corchetes) y separadores (comas, dos puntos)
                parts.append(token.value)

        result = "".join(parts)

        # DEBUG: Descomentar para ver el resultado final
        # print(f"[FINALIZE] Result: {result[:200]}...")

        return result
