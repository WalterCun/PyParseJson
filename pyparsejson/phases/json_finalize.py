from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType


class JSONFinalize:
    """
    Convierte la lista de tokens reparada en un string JSON estricto.
    """

    @staticmethod
    def process(context: Context) -> str:
        parts = []
        for token in context.tokens:
            if token.type == TokenType.STRING:
                # Asegurar que tenga comillas dobles
                val = token.value
                if val.startswith("'") and val.endswith("'"):
                    val = '"' + val[1:-1].replace('"', '\\"') + '"'
                elif not val.startswith('"'):
                    val = f'"{val}"'
                parts.append(val)
            elif token.type == TokenType.BOOLEAN:
                parts.append(token.value.lower())  # true/false
            elif token.type == TokenType.NULL:
                parts.append("null")
            elif token.type == TokenType.DATE:
                # Fechas: Se convierten a string JSON
                val = token.value
                parts.append(f'"{val}"')
            else:
                parts.append(token.value)

        return "".join(parts)