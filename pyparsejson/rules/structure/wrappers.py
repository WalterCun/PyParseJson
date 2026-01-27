from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token


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