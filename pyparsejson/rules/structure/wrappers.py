from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=1)
class WrapRootObjectRule(Rule):
    """
    Envuelve el contenido en {} si parece ser un objeto suelto (pares clave-valor)
    y no empieza ya con { o [.

    MEJORA INTELIGENTE:
    Ignora textos que parecen oraciones o comandos (ej. SQL) verificando si hay
    estructura inmediatamente después de la primera palabra.
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if not tokens:
            return False

        # Si ya empieza como objeto o array, NO aplicar
        if tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET):
            return False

        # Si no hay pares clave:valor en el root → NO aplicar
        # (Esta es la regla original básica)
        if not any(t.type in (TokenType.COLON, TokenType.ASSIGN) for t in tokens):
            return False

        # --- NUEVO FILTRO INTELIGENTE ---
        # Si el primer token es una palabra (ej. "hola", "INSERT", "SELECT")
        # verificamos si hay estructura inmediata.
        if tokens[0].type == TokenType.BARE_WORD:
            # Miramos los siguientes 3 tokens.
            # Si no encontramos :, =, { o [ en las primeras posiciones,
            # asumimos que es texto libre (oración, SQL, etc) y no envolvemos.
            limit = min(3, len(tokens))
            found_structure_early = False

            for i in range(1, limit):
                next_token = tokens[i]
                if next_token.type in (
                        TokenType.COLON,
                        TokenType.ASSIGN,
                        TokenType.LBRACE,
                        TokenType.LBRACKET
                ):
                    found_structure_early = True
                    break

            # Si no hay estructura cerca del inicio, lo dejamos pasar (return False)
            # El parser fallará con FAILED_UNRECOVERABLE, lo cual es correcto.
            if not found_structure_early:
                return False

        # Si pasó los filtros, aplicar envoltura
        return True

    def apply(self, context: Context):
        l_brace = Token(TokenType.LBRACE, "{", "{", 0)
        r_brace = Token(TokenType.RBRACE, "}", "}", context.tokens[-1].position + 1)

        context.tokens.insert(0, l_brace)
        context.tokens.append(r_brace)

        context.mark_changed()
        context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "normalization"], priority=30)
class QuoteKeysRule(Rule):
    """
    Convierte claves sin comillas en strings JSON válidos.
    user: -> "user":
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i, token in enumerate(tokens[:-1]):
            if token.type == TokenType.BARE_WORD and tokens[i + 1].type == TokenType.COLON:
                return True
        return False

    def apply(self, context: Context):
        changed = False
        for i, token in enumerate(context.tokens[:-1]):
            if token.type == TokenType.BARE_WORD and context.tokens[i + 1].type == TokenType.COLON:
                token.type = TokenType.STRING
                token.value = f'"{token.value}"'
                token.raw_value = token.value
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)