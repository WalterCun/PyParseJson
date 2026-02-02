# Path: pyparsejson\rules\structure\cleanup.py
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token
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
    Elimina texto no-JSON del inicio.

    ESTRATEGIA:
    1. Detectar palabras clave SQL/lenguajes de programación
    2. Si el texto empieza con ellas, marcar como NO-JSON
    3. Buscar primera estructura válida ({ o [ o clave:)
    4. Cortar todo lo anterior
    """

    # Lista negra expandida
    NON_JSON_STARTERS = {
        # SQL
        'insert', 'select', 'update', 'delete', 'create', 'alter', 'drop',
        'grant', 'revoke', 'truncate', 'merge', 'call', 'exec',

        # Programación
        'function', 'def', 'class', 'import', 'from', 'return', 'if',
        'else', 'for', 'while', 'do', 'switch', 'case', 'try', 'catch',

        # Lenguaje natural (español/inglés)
        'hola', 'hello', 'hey', 'hi', 'que', 'what', 'esto', 'this',
        'el', 'la', 'the', 'un', 'una', 'a', 'an', 'es', 'is',

        # Comandos
        'echo', 'print', 'console', 'log', 'debug'
    }

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 2:
            return False

        # Ya empieza bien → no aplicar
        if tokens[0].type in (TokenType.LBRACE, TokenType.LBRACKET):
            return False

        # Primera palabra es clave válida → no aplicar
        if tokens[0].type == TokenType.BARE_WORD:
            if len(tokens) > 1 and tokens[1].type in (TokenType.COLON, TokenType.ASSIGN):
                return False

        # Primera palabra está en lista negra → aplicar
        if tokens[0].type == TokenType.BARE_WORD and tokens[0].value.lower() in self.NON_JSON_STARTERS:
            return True

        # Buscar si hay estructura válida más adelante
        for i in range(1, min(len(tokens), 10)):  # Solo buscar en primeros 10 tokens
            if tokens[i].type in (TokenType.LBRACE, TokenType.LBRACKET):
                return True
            if tokens[i].type == TokenType.BARE_WORD:
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                    return True

        return False

    def apply(self, context: Context):
        tokens = context.tokens

        # ESTRATEGIA 1: Si empieza con palabra de lista negra, eliminar TODO
        if tokens[0].type == TokenType.BARE_WORD and tokens[0].value.lower() in self.NON_JSON_STARTERS:
            # Buscar si hay ALGO salvable después
            found_structure = False
            start_idx = 0

            for i in range(1, len(tokens)):
                if tokens[i].type in (TokenType.LBRACE, TokenType.LBRACKET):
                    start_idx = i
                    found_structure = True
                    break
                if tokens[i].type == TokenType.BARE_WORD:
                    if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                        start_idx = i
                        found_structure = True
                        break

            if found_structure:
                context.tokens = tokens[start_idx:]
            else:
                # No hay nada salvable → vaciar
                context.tokens = []

            context.mark_changed()
            context.record_rule(self.name)
            return

        # ESTRATEGIA 2: Basura antes de estructura válida
        for i in range(1, len(tokens)):
            if tokens[i].type in (TokenType.LBRACE, TokenType.LBRACKET):
                context.tokens = tokens[i:]
                context.mark_changed()
                context.record_rule(self.name)
                return

            if tokens[i].type == TokenType.BARE_WORD:
                if i + 1 < len(tokens) and tokens[i + 1].type == TokenType.COLON:
                    context.tokens = tokens[i:]
                    context.mark_changed()
                    context.record_rule(self.name)
                    return


@RuleRegistry.register(tags=["structure", "cleanup"], priority=5)
class StripCommentsRule(Rule):
    """
    Elimina comentarios C-style (// hasta fin de línea) y bloque (/* ... */).
    Ej: "user: admin // comment" → "user: admin"
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens

        # Optimización: Si no hay tokens que parezcan comentarios, salir rápido
        # Buscamos // o /* en valores o tokens UNKNOWN consecutivos
        has_potential_comment = False
        for i in range(len(tokens)):
            t = tokens[i]
            # Si es STRING, ignorar contenido (REGLA DE ORO: STRING es atómico)
            if t.type == TokenType.STRING:
                continue

            # Detectar // como dos tokens UNKNOWN consecutivos
            if (i + 1 < len(tokens) and
                    t.type == TokenType.UNKNOWN and t.value == "/" and
                    tokens[i + 1].type == TokenType.UNKNOWN and tokens[i + 1].value == "/"):
                has_potential_comment = True
                break

            # Detectar // o /* dentro de BARE_WORD o UNKNOWN
            if t.type in (TokenType.BARE_WORD, TokenType.UNKNOWN):
                if "//" in t.value or "/*" in t.value or "*/" in t.value:
                    has_potential_comment = True
                    break

        return has_potential_comment

    def apply(self, context: Context):
        new_tokens = []
        skip_until_newline = False
        skip_block = False
        i = 0

        while i < len(context.tokens):
            token = context.tokens[i]

            # REGLA DE ORO: Si es STRING, se preserva intacto SIEMPRE
            # (A menos que estemos ya dentro de un bloque de comentario saltando todo)
            if not skip_until_newline and not skip_block:
                if token.type == TokenType.STRING:
                    new_tokens.append(token)
                    i += 1
                    continue

            # NUEVO: Detectar // como dos tokens UNKNOWN consecutivos
            if (not skip_until_newline and not skip_block and
                    i + 1 < len(context.tokens) and
                    token.type == TokenType.UNKNOWN and token.value == "/" and
                    context.tokens[i + 1].type == TokenType.UNKNOWN and context.tokens[i + 1].value == "/"):
                # Encontrado //, saltar hasta fin de línea
                i += 2  # Saltar ambos "/"
                skip_until_newline = True
                continue

            # Manejar comentarios de línea // (cuando están en un solo token BARE_WORD o UNKNOWN)
            if not skip_until_newline and not skip_block and token.type in (TokenType.BARE_WORD, TokenType.UNKNOWN):
                if "//" in token.value:
                    parts = token.value.split("//", 1)
                    if parts[0].strip():
                        new_tokens.append(Token(
                            TokenType.BARE_WORD if token.type == TokenType.BARE_WORD else token.type,
                            parts[0].strip(),
                            parts[0].strip(),
                            token.position
                        ))
                    skip_until_newline = True
                    i += 1
                    continue

            # Manejar inicio de bloque /*
            if not skip_until_newline and not skip_block and token.type in (TokenType.BARE_WORD, TokenType.UNKNOWN):
                if "/*" in token.value:
                    skip_block = True
                    i += 1
                    continue

            # Manejar fin de bloque */
            if skip_block and token.type in (TokenType.BARE_WORD, TokenType.UNKNOWN):
                if "*/" in token.value:
                    skip_block = False
                    i += 1
                    continue

            # Saltar tokens dentro de comentario de línea
            if skip_until_newline:
                if '\n' in token.value or token.value.strip() == "":
                    skip_until_newline = False
                i += 1
                continue

            # Saltar tokens dentro de bloque
            if skip_block:
                i += 1
                continue

            # Token normal, agregar
            new_tokens.append(token)
            i += 1

        if len(new_tokens) != len(context.tokens):
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)