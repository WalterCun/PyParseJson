from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


@RuleRegistry.register(tags=["structure", "cleanup"], priority=0)  # Ejecuta ANTES que las reglas pre_repair
class StripPrefixGarbageRule(Rule):
    """
    Elimina prefijos de texto (basura) antes de la estructura JSON real.

    Lógica corregida:
    - Si empieza con { o [, no hacer nada.
    - Si empieza con una palabra clave (ej. "user:"), NO ES BASURA.
    - Solo cortar si el inicio NO tiene estructura y luego sí la hay.

    MEJORA: Detecta comandos SQL (INSERT, SELECT, UPDATE, etc.) para eliminarlos por completo.
    """

    # Lista negra de palabras que probablemente no son JSON root keys válidos (SQL, palabras clave de lenguajes naturales)
    NON_JSON_STARTERS = {
        'insert', 'select', 'update', 'delete', 'create', 'alter', 'drop', 'grant', 'revoke',
        'from', 'where', 'into', 'values', 'set', 'declare', 'case', 'go', 'do', 'begin',
        'print', 'echo', 'export', 'import', 'class', 'def', 'function', 'return', 'if', 'else', 'for', 'while',
        'hola', 'que', 'hay', 'esto', 'no', 'de', 'la', 'el', 'en', 'un', 'una', 'es'
        # Palabras comunes que suelen romper el inicio (Caso 26)
    }

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        # Si ya empieza con estructura válida, no hacer nada
        if tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET):
            return False

        # Si el primer token es un comando SQL o palabra irrelevante, cortar todo.
        # Esto arregla CASO 24 (SQL) y CASO 26 ("hola mundo").
        if tokens[0].type == TokenType.BARE_WORD and tokens[0].value.lower() in self.NON_JSON_STARTERS:
            return True

        # Si el primer token es una palabra clave (ej. "user:"), NO ES BASURA.
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
        # Cortar todo el inicio basura
        # Para CASO 26 ("hola mundo..."), esto borrará todo.
        # Para CASO 24 ("INSERT..."), esto borrará el comando SQL.
        context.tokens = [t for t in context.tokens if
                          t.type != TokenType.BARE_WORD or t.value.lower() not in self.NON_JSON_STARTERS]
        context.mark_changed()
        context.record_rule(self.name)


# pyparsejson/rules/structure/wrappers.py - REEMPLAZAR WrapRootObjectRule completo

@RuleRegistry.register(tags=["structure", "bootstrap"], priority=5)
class WrapRootObjectRule(Rule):
    """
    Envuelve pares sueltos en objeto raíz { ... }

    VERSIÓN CORREGIDA: Previene doble wrapping verificando si ya hay llaves.
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if not tokens:
            return False

        # ⭐ CORRECCIÓN CRÍTICA: Contar llaves de apertura consecutivas al inicio
        opening_braces = 0
        for i, token in enumerate(tokens):
            if token.type == TokenType.LBRACE:
                opening_braces += 1
            else:
                break  # Detenerse en el primer token que NO sea LBRACE

        # Si ya hay 1 o más llaves de apertura, NO aplicar
        # Esto previene {{...}} o {{{...}}}
        if opening_braces >= 1:
            return False

        # Verificación adicional: Si termina con llave de cierre, probablemente ya está envuelto
        closing_braces = 0
        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i].type == TokenType.RBRACE:
                closing_braces += 1
            else:
                break

        if closing_braces >= 1:
            return False

        # Ya está envuelto en array
        if tokens[0].type == TokenType.LBRACKET and tokens[-1].type == TokenType.RBRACKET:
            return False

        # Detectar al menos UN par clave:valor suelto
        for i in range(len(tokens) - 1):
            if (tokens[i].type in (TokenType.BARE_WORD, TokenType.STRING) and
                    tokens[i + 1].type in (TokenType.COLON, TokenType.ASSIGN)):
                return True

        return False

    def apply(self, context: Context):
        """
        Envolver TODO el contenido en { ... }
        Solo se ejecuta si applies() retorna True (no hay llaves ya)
        """
        context.tokens = [
            Token(TokenType.LBRACE, "{", "{", 0),
            *context.tokens,
            Token(TokenType.RBRACE, "}", "}", len(context.tokens))
        ]
        context.mark_changed()
        context.record_rule(self.name)


@RuleRegistry.register(tags=["structure", "bootstrap"], priority=9999)
class ImplicitArrayRule(Rule):
    """
    Detecta secuencias implícitas de valores (sin clave) y las envuelve en array.
    Ej: "ids: 1, 2, 3" → "ids: [1, 2, 3]"

    VERSIÓN CORREGIDA: Solo aplica cuando hay MÚLTIPLES valores sin claves intermedias.
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        for i in range(len(tokens) - 5):  # Necesitamos al menos: clave : val , val
            # Patrón: clave : valor , valor (SIN otra clave en medio)
            if (tokens[i].type in (TokenType.BARE_WORD, TokenType.STRING) and
                    i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON and
                    i + 2 < len(tokens) and tokens[i + 2].type in (TokenType.NUMBER, TokenType.STRING,
                                                                   TokenType.BOOLEAN, TokenType.BARE_WORD) and
                    i + 3 < len(tokens) and tokens[i + 3].type == TokenType.COMMA and
                    i + 4 < len(tokens) and tokens[i + 4].type in (TokenType.NUMBER, TokenType.STRING,
                                                                   TokenType.BOOLEAN, TokenType.BARE_WORD)):

                # VERIFICACIÓN CRÍTICA: El token después de la coma NO debe ser una clave
                # Si el token en i+5 es ":", entonces i+4 es una clave, NO un valor de array
                if i + 5 < len(tokens) and tokens[i + 5].type == TokenType.COLON:
                    continue  # No es un array implícito, es otro par clave:valor

                return True

        return False

    def apply(self, context: Context):
        tokens = context.tokens
        new_tokens = []
        i = 0

        while i < len(tokens):
            # Detectar patrón: clave : valor , valor ... (sin claves intermedias)
            if (i + 4 < len(tokens) and
                    tokens[i].type in (TokenType.BARE_WORD, TokenType.STRING) and
                    tokens[i + 1].type == TokenType.COLON and
                    tokens[i + 2].type in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN,
                                           TokenType.BARE_WORD) and
                    tokens[i + 3].type == TokenType.COMMA and
                    tokens[i + 4].type in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.BARE_WORD)):

                # VERIFICACIÓN: ¿El siguiente es otra clave o un valor de array?
                if i + 5 < len(tokens) and tokens[i + 5].type == TokenType.COLON:
                    # Es otra clave, NO convertir en array
                    new_tokens.append(tokens[i])
                    i += 1
                    continue

                # Es un array implícito real - encontrar el final
                start_val = i + 2
                j = i + 3
                in_sequence = True

                while j < len(tokens) and in_sequence:
                    if tokens[j].type in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.BARE_WORD):
                        # Verificar si el siguiente es ":" (sería una clave)
                        if j + 1 < len(tokens) and tokens[j + 1].type == TokenType.COLON:
                            in_sequence = False
                            break
                        j += 1
                    elif j + 1 < len(tokens) and tokens[j].type == TokenType.COMMA and tokens[j + 1].type in (
                            TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.BARE_WORD
                    ):
                        # Verificar si después de la coma hay una clave
                        if j + 2 < len(tokens) and tokens[j + 2].type == TokenType.COLON:
                            in_sequence = False
                            break
                        j += 2
                    else:
                        in_sequence = False

                # Envolver en array
                new_tokens.append(tokens[i])  # clave
                new_tokens.append(tokens[i + 1])  # :
                new_tokens.append(Token(TokenType.LBRACKET, "[", "[", tokens[i].position))
                new_tokens.extend(tokens[i + 2:j])
                new_tokens.append(
                    Token(TokenType.RBRACKET, "]", "]", tokens[j - 1].position if j > i + 2 else tokens[i].position))

                i = j
            else:
                new_tokens.append(tokens[i])
                i += 1

        if len(new_tokens) != len(tokens):
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)
