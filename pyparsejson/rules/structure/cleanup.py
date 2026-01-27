from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


@RuleRegistry.register(tags=["structure", "cleanup"], priority=0)
class RemoveTrailingCommasRule(Rule):

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i in range(len(tokens) - 1):
            if tokens[i].type == TokenType.COMMA and tokens[i + 1].type in (
                    TokenType.RBRACE,
                    TokenType.RBRACKET,
            ):
                return True
        return False

    def apply(self, context: Context):
        tokens = context.tokens
        new_tokens = []

        i = 0
        while i < len(tokens):
            if (
                    tokens[i].type == TokenType.COMMA
                    and i + 1 < len(tokens)
                    and tokens[i + 1].type in (TokenType.RBRACE, TokenType.RBRACKET)
            ):
                i += 1
                continue
            new_tokens.append(tokens[i])
            i += 1

        context.tokens = new_tokens
        context.mark_changed()
        context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "cleanup"], priority=0)
class StripPrefixGarbageRule(Rule):
    """
    Elimina prefijos de texto (basura) antes de la estructura JSON real.

    Ejemplos:
    1. "hola mundo {key: val}" -> "{key: val}"
    2. "log inicio [1, 2, 3]" -> "[1, 2, 3]"
    3. "prefijo clave: valor" -> "clave: valor"
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        # Si ya empieza con estructura válida, no hacer nada
        if tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET):
            return False

        # Buscar si hay algo que parezca estructura después del inicio
        # 1. Buscar { o [
        # 2. Buscar "palabra" :
        for i in range(1, len(tokens)):
            if tokens[i].type in (TokenType.LBRACE, TokenType.LBRACKET):
                return True  # Encontramos estructura posterior, hay que borrar prefijo

            # Buscar clave: valor
            if tokens[i].type == TokenType.BARE_WORD:
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                    return True  # Encontramos par clave:valor, borramos lo anterior

        return False

    def apply(self, context: Context):
        tokens = context.tokens
        new_tokens = []
        start_index = 0

        # Determinar desde qué índice empieza realmente el JSON
        for i in range(len(tokens)):
            # Opción A: Inicio de objeto/array
            if tokens[i].type in (TokenType.LBRACE, TokenType.LBRACKET):
                start_index = i
                break

            # Opción B: Inicio de par clave:valor (si no hay llaves)
            # Solo si no estamos al principio (índice 0)
            if tokens[i].type == TokenType.BARE_WORD and i > 0:
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                    # Este es el inicio real (la clave)
                    start_index = i
                    break

        # Slice de la lista de tokens
        if start_index > 0:
            context.tokens = tokens[start_index:]
            context.mark_changed()
            context.record_rule(self.name)