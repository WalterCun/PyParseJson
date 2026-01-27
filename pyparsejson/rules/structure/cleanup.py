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

    Lógica corregida:
    - Si empieza con { o [, no hacer nada.
    - Si empieza con una palabra clave (ej. "user:"), NO ES BASURA.
    - Solo cortar si el inicio NO tiene estructura y luego sí la hay.
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        # Si ya empieza con estructura válida, no hacer nada
        if tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET):
            return False

        # MIRAR SI EL INICIO ES UNA CLAVE VÁLIDA (palabra + : o =)
        # Si lo es, no es basura, es el inicio del objeto JSON.
        if tokens[0].type == TokenType.BARE_WORD:
            if len(tokens) > 1 and tokens[1].type in (TokenType.COLON, TokenType.ASSIGN):
                return False  # No aplicar, el inicio es válido (ej: user: admin)

        # Si llegamos aquí, probablemente hay basura al inicio.
        # Buscamos estructura posterior para cortar prefijo.
        for i in range(1, len(tokens)):
            if tokens[i].type in (TokenType.LBRACE, TokenType.LBRACKET):
                return True

                # Buscar clave: valor
            if tokens[i].type == TokenType.BARE_WORD:
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                    return True

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
            if tokens[i].type == TokenType.BARE_WORD:
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                    start_index = i
                    break

        # Slice de la lista de tokens
        if start_index > 0:
            context.tokens = tokens[start_index:]
            context.mark_changed()
            context.record_rule(self.name)