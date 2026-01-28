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
    Inserta comas faltantes entre pares clave:valor.

    Detecta:
    - Objetos: user: admin, active: si.
    - Listas implícitas: ids: 1, 2, 3 (comas entre 1, 2, 3 y 2, 3).
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

            # Necesitamos mirar hacia adelante para decidir si insertar coma
            if i + 1 >= len(context.tokens):
                i += 1
                continue

            next_token = context.tokens[i + 1]
            next_next_token = context.tokens[i + 2] if i + 2 < len(context.tokens) else None

            # Detectar si el token actual es el final de un valor (ej: "admin")
            is_current_value_end = current_token.type in (
                TokenType.STRING,
                TokenType.NUMBER,
                TokenType.BOOLEAN,
                TokenType.NULL,
                TokenType.RBRACE,
                TokenType.RBRACKET,
                TokenType.BARE_WORD
            )

            # Detectar si el siguiente token es el inicio de una nueva clave (ej. "active:")
            is_next_key = next_token.type in (TokenType.BARE_WORD, TokenType.STRING)

            # Caso 1: Valor + Clave (ej: admin, active: si). Insertar coma.
            # Caso 2: Valor + [ (ej: permissions: (read...
            # Caso 3: ] + Clave (ej: ] active).
            # Caso 4: Valor + }, (ej: status: ok, ). Ignorar }.

            if is_current_value_end and is_next_key:
                # Si hay un separador adicional (ej. `user // superuser`), NO insertar coma.
                # Se maneja en StripPrefixGarbageRule para los comentarios.
                if next_next_token and next_next_token.type == TokenType.BARE_WORD:
                    pass
                elif next_next_token and next_next_token.type == TokenType.COLON:
                    # "deposito fecha='2026...'" -> No insertar coma si hay igual
                    pass

                # Insertar coma
                comma_token = Token(TokenType.COMMA, ",", ",", current_token.position + 1)
                new_tokens.append(comma_token)
                changed = True

            i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "values"], priority=15)
class TupleToListRule(Rule):
    def applies(self, context: Context) -> bool:
        return any(t.type in (TokenType.LPAREN, TokenType.RPAREN) for t in context.tokens)

    def apply(self, context: Context):
        changed = False
        for token in context.tokens:
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
        if changed:
            context.mark_changed()
            context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "normalization"], priority=30)
class QuoteKeysRule(Rule):
    """Envuelve TODAS las claves en comillas dobles (requerido por JSON estándar)"""
    def applies(self, context: Context) -> bool:
        return any(
            i + 1 < len(context.tokens) and
            context.tokens[i].type in (TokenType.BARE_WORD, TokenType.STRING) and
            context.tokens[i + 1].type == TokenType.COLON
            for i in range(len(context.tokens))
        )

    def apply(self, context: Context):
        new_tokens = []
        for i, token in enumerate(context.tokens):
            if (token.type in (TokenType.BARE_WORD, TokenType.STRING) and
                i + 1 < len(context.tokens) and
                context.tokens[i + 1].type == TokenType.COLON):
                # Normalizar clave a comillas dobles
                clean_val = token.value.strip('"\'')
                new_tokens.append(Token(TokenType.STRING, f'"{clean_val}"', f'"{clean_val}"', token.position))
            else:
                new_tokens.append(token)
        context.tokens = new_tokens
        context.mark_changed()
        context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "cleanup"], priority=99)
class BalanceBracketsRule(Rule):
    """Asegura balance final de llaves y corchetes"""

    def applies(self, context: Context) -> bool:
        # Ejecutar solo en la última iteración
        return context.current_iteration == context.max_iterations

    def apply(self, context: Context):
        stack = []
        for token in context.tokens:
            if token.type == TokenType.LBRACE:
                stack.append(TokenType.RBRACE)
            elif token.type == TokenType.LBRACKET:
                stack.append(TokenType.RBRACKET)
            elif token.type in (TokenType.RBRACE, TokenType.RBRACKET) and stack:
                stack.pop()

        # Añadir cierres faltantes
        while stack:
            close_type = stack.pop()
            char = "}" if close_type == TokenType.RBRACE else "]"
            context.tokens.append(Token(close_type, char, char, len(context.tokens)))
            context.mark_changed()