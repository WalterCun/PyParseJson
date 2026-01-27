from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=10)
class EqualToColonRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type == TokenType.ASSIGN for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
            if token.type == TokenType.ASSIGN:
                token.type = TokenType.COLON
                token.value = ":"
                token.raw_value = ":"
                changed = True

        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "pre_repair"], priority=20)
class AddMissingCommasRule(Rule):
    """
    Lógica mejorada:
    - Detecta [ y ] como fin de valor (para arrays implícitos).
    - Evita insertar comas si estamos dentro de una estructura.
    """

    def applies(self, context: Context) -> bool:
        return len(context.tokens) > 1

    def apply(self, context: Context):
        new_tokens = []
        i = 0
        changed = False

        while i < len(context.tokens):
            current_token = context.tokens[i]
            new_tokens.append(current_token)

            if i + 1 < len(context.tokens):
                next_token = context.tokens[i + 1]

                # --- MODIFICACIÓN PRINCIPAL ---
                # Añadimos RBRACE y RBRACKET a la lista de "Finales de Valor"
                is_current_value_end = current_token.type in (
                    TokenType.STRING,
                    TokenType.NUMBER,
                    TokenType.BOOLEAN,
                    TokenType.NULL,
                    # ... (ver abajo)
                )

                # IMPORTANTE: Si el siguiente es RBRACKET (cierre de array), contamos la coma.
                is_next_closure = next_token.type in (TokenType.RBRACE, TokenType.RBRACKET)

                # --- LÓGICA DE ARRAYS IMPLÍCITOS ---
                # Detecta estructuras como: ids: 1, 2, 3
                # 'ids' es KEY, '1' es VALUE, '2' es KEY.
                # '3' es VALUE.
                # Necesitamos insertar coma entre '1' y '2', y entre '2' y '3'.
                #
                # Detectamos si estamos en un contexto que parece una lista implícita:
                # No hay llaves a la vista.
                is_in_implicit_array = (
                        not context.tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET) and
                        context.tokens[0].type == TokenType.BARE_WORD
                )

                # Si estamos en una lista implícita, el anterior era un valor.
                # El actual es KEY.
                is_current_value_in_array = is_in_implicit_array and i > 0

                if is_current_value_end and is_current_value_in_array:
                    # Si el siguiente es otro valor (palabra o número), insertar coma.
                    is_next_value = next_token.type in (TokenType.BARE_WORD, TokenType.NUMBER)
                    if is_next_value:
                        comma_token = Token(TokenType.COMMA, ",", ",", current_token.position + 1)
                        new_tokens.append(comma_token)
                        changed = True
                        continue  # Saltamos el incremento normal 'i += 1'

            i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "values"], priority=15)
class TupleToListRule(Rule):
    def applies(self, context: Context) -> bool:
        # Solo aplicamos si hay paréntesis
        return any(t.type in (TokenType.LPAREN, TokenType.RPAREN) for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        i = 0
        while i < len(context.tokens):
            token = context.tokens[i]

            # SOLO convertimos ( y filtramos) paréntesis que NO estén dentro de strings
            # Si el token anterior y siguiente son comillas o vacíos, probablemente es un string que contenía paréntesis.
            prev_is_string_or_space = (
                    i > 0 and
                    context.tokens[i - 1].type in (TokenType.STRING, TokenType.COMMA, TokenType.LBRACE,
                                                   TokenType.LBRACKET)
            )

            if token.type in (TokenType.LPAREN, TokenType.RPAREN) and not prev_is_string_or_space:
                if token.type == TokenType.LPAREN:
                    token.type = TokenType.LBRACKET
                    token.value = "["
                    token.raw_value = "["
                    changed = True
                elif token.type == TokenType.RPAREN:
                    token.type = TokenType.RBRACKET
                    token.value = "]"
                    token.raw_value = "]"
                    changed = True

            i += 1

        if changed:
            context.mark_changed()
            context.record_rule(self.name)