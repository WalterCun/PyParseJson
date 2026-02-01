# Size: 18.26 KB, Lines: 241

# Path: pyparsejson\rules\structure\wrappers.py
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


# -----------------------------------------------------------------
# REGLA: RootObjectRule (NUEVA)
# -----------------------------------------------------------------
@RuleRegistry.register(tags=["structure", "bootstrap"], priority=1)
class RootObjectRule(Rule):
    """
    Envuelve la lista completa de tokens en un objeto JSON raíz { ... } si no está envuelta.
    Esto soluciona los casos "key: val, key: val" que se quedan colgando al final porque el parser espera una estructura de objeto completa.
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        # Si ya tiene llave/corchete raíz, no hacer nada
        if tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET):
            return False

        # Detectar si el primer token es BARE_WORD y el segundo es COLON.
        # Esto sugiere 'key: ...'
        # Nota: Es una heurística débil pero efectiva para Frankenstein JSONs simples.
        if (tokens[0].type == TokenType.BARE_WORD and tokens[1].type == TokenType.COLON):
            # Verificar si parece una estructura de valores múltiples o anidación.
            # Si el último token es un valor, probablemente es un objeto.
            # Si el último token es un COLON, probablemente es una estructura anidada.
            # Vamos a envolver todo, si tiene al menos 3 claves separadas.
            colon_count = sum(1 for t in tokens if t.type == TokenType.COLON)
            if colon_count >= 2:
                return True

        # Detectar implícitos: key: 1, 2, 3
        # Solo envolver si NO hay estructura existente.
        # Si ya hay estructura, no hacer nada (para evitar re-empaquetar).
        has_structure = any(t.type in (TokenType.LBRACE, TokenType.LBRACKET, TokenType.LBRACE, TokenType.LBRACKET) for t in tokens)
        if has_structure:
            return False

        return True

    def apply(self, context: Context):
        tokens = context.tokens

        # Buscar el final de la secuencia para envolver
        # Si hay múltiples colones al final (ej: key1:1, key2:2), no envolver.
        # Si hay un solo colon y termina en valor, envolver.
        colon_count = sum(1 for t in tokens if t.type == TokenType.COLON)

        # Si es un solo par y no tiene llaves
        if colon_count == 1 and not any(t.type == TokenType.LBRACE for t in tokens):
            # Envolver en { ... }
            l_brace = Token(TokenType.LBRACE, "{", "{", tokens[0].position)
            r_brace = Token(TokenType.RBRACE, "}", "}", len(tokens))

            new_tokens = [l_brace] + tokens + [r_brace]
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)
            return

        # Si hay múltiples pares (ej: key1:1, key2:2), envolver en { ... }
        # Esto es más agresivo pero necesario para Caso 15, 16, etc.
        if colon_count >= 2 and not any(t.type == TokenType.LBRACE for t in tokens):
            l_brace = Token(TokenType.LBRACE, "{", "{", tokens[0].position)
            r_brace = Token(TokenType.RBRACE, "}", "}", len(tokens))
            new_tokens = [l_brace] + tokens + [r_brace]
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)


# -----------------------------------------------------------------
# REGLA: EnsureTrailingCommasBeforeEndRule (NUEVA)
# -----------------------------------------------------------------
@RuleRegistry.register(tags=["structure", "cleanup"], priority=100)
class EnsureTrailingCommasBeforeEndRule(Rule):
    """
    Limpia tokens basura al final del documento que impiden el cierre.
    El objetivo es convertir {key1: val1, key2: val2} en {key1: val1, key2: val2, } (coma final).
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        # Si ya termina con } o ], y el anterior es un valor (no ), añadir ,
        if (tokens[-1].type in (TokenType.RBRACE, TokenType.RBRACKET)):
            if len(tokens) > 1 and tokens[-2].type in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.NULL):
                return True

        # Si termina en valor simple y NO es un valor vacío, añadir ,}
        # Esto arregla {"user":"admin","active":true} → {"user":"admin","active":true, }
        if tokens[-1].type in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.NULL):
            if tokens[-1].value not in ("true", "false", "null", ""):
                # No es un valor vacío.
                return True

        return False

    def apply(self, context: Context):
        tokens = context.tokens
        changed = False

        # 1. Coma antes de } o ] (excepto si es JSON vacío)
        if len(tokens) >= 2 and tokens[-1].type in (TokenType.RBRACE, TokenType.RBRACKET):
            # Comprobar token anterior
            if len(tokens) >= 2:
                prev = tokens[-2]
                if prev.type not in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.NULL):
                    # Es valor, no una com.
                    comma = Token(
                        type=TokenType.COMMA,
                        value=",",
                        raw_value=",",
                        position=len(tokens),
                        line=0,
                        column=0
                    )
                    # Insertar coma antes del cierre
                    tokens.insert(-1, comma)
                    changed = True

        # 2. Coma al final si es un valor simple
        # Nota: Esto NO arregla key1: val, key2: val2 porque se detecta antes de RootObjectRule.
        # Pero arregla el trunco del Caso 1: {"user":"admin","active":true}
        if not changed:
            if tokens[-1].type in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.NULL):
                if tokens[-1].value not in ("true", "false", "null", ""):
                    tokens.append(
                        Token(
                            type=TokenType.COMMA,
                            value=",",
                            raw_value=",",
                            position=len(tokens),
                            line=0,
                            column=0
                        ))
                    changed = True

        if changed:
            context.tokens = tokens
            context.mark_changed()
            context.record_rule(self.name)
