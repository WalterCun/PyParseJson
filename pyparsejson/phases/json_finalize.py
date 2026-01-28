from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType


class JSONFinalize:
    """
    Convierte la lista de tokens reparada en un string JSON sintácticamente estricto.
    Esta es la última fase antes de intentar el parseo final con `json.loads`.
    """

    @staticmethod
    def process(context: Context) -> str:
        """
        Procesa la lista de tokens y devuelve un string JSON.
        """
        parts = []
        for token in context.tokens:
            if token.type == TokenType.STRING:
                # Asegurar que los strings tengan comillas dobles y escapar las internas
                val = token.value
                if val.startswith("'") and val.endswith("'"):
                    # Convertir comillas simples a dobles
                    val = '"' + val[1:-1].replace('"', '\\"') + '"'
                elif not val.startswith('"'):
                    # Añadir comillas a palabras que deberían ser strings
                    val = f'"{val}"'
                parts.append(val)
            elif token.type == TokenType.BOOLEAN:
                # Estandarizar a minúsculas (true/false)
                parts.append(token.value.lower())
            elif token.type == TokenType.NULL:
                # Estandarizar a "null"
                parts.append("null")
            elif token.type == TokenType.DATE:
                # Las fechas se convierten a strings JSON
                parts.append(f'"{token.value}"')
            else:
                # El resto de tokens (números, llaves, comas, etc.) se mantienen igual
                parts.append(token.value)

        return "".join(parts)
