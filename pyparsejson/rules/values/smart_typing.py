import re
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


@RuleRegistry.register(tags=["values", "smart"], priority=55)
class SmartTypingRule(Rule):
    """
    Utiliza el contexto del nombre de la clave para inferir el tipo correcto del valor.
    Esto ayuda a evitar ambigüedades como códigos postales tratados como números o
    emails tratados como palabras clave.
    """

    # Patrones de nombres de claves que sugieren que el valor DEBE ser un string
    STRING_HINTS = re.compile(
        r'(date|time|at|timestamp|created|updated|birth|'  # Fechas
        r'email|mail|user|login|id|uuid|key|code|'  # Identificadores
        r'phone|cel|mobile|zip|postal|'  # Contacto
        r'name|title|desc|content|'  # Texto libre
        r'url|uri|path|file)'  # Rutas
    )

    # Patrones de nombres de claves que sugieren que el valor DEBE ser un número
    NUMBER_HINTS = re.compile(
        r'(count|amount|total|price|cost|qty|quantity|'  # Finanzas/Cantidad
        r'lat|lng|longitude|latitude|'  # Coordenadas
        r'score|weight|height|width|size)'  # Medidas
    )

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        if len(tokens) < 3:
            return False

        for i in range(len(tokens) - 2):
            key_token = tokens[i]
            sep_token = tokens[i + 1]

            is_key = key_token.type in (TokenType.STRING, TokenType.BARE_WORD)
            is_separator = sep_token.type in (TokenType.COLON, TokenType.ASSIGN)

            if is_key and is_separator:
                val_token = tokens[i + 2]
                # --- IMPORTANTE: Ignoramos si ya es un String o Date procesado ---
                if val_token.type in (TokenType.BARE_WORD, TokenType.NUMBER):
                    key_name = key_token.value.strip('"').lower()
                    if self.STRING_HINTS.search(key_name) or self.NUMBER_HINTS.search(key_name):
                        return True
        return False

    def apply(self, context: Context):
        changed = False
        tokens = context.tokens
        new_tokens = []

        i = 0
        while i < len(tokens):
            current = tokens[i]
            new_tokens.append(current)

            if i + 2 < len(tokens):
                next_sep = tokens[i + 1]
                next_val = tokens[i + 2]

                is_key = current.type in (TokenType.STRING, TokenType.BARE_WORD)
                is_separator = next_sep.type in (TokenType.COLON, TokenType.ASSIGN)

                if is_key and is_separator:
                    key_name = current.value.strip('"').lower()

                    # 1. Si la clave sugiere STRING y el valor es BareWord o Number
                    if self.STRING_HINTS.search(key_name):
                        if next_val.type == TokenType.BARE_WORD:
                            next_val.type = TokenType.STRING
                            next_val.value = f'"{next_val.value}"'
                            next_val.raw_value = next_val.value
                            changed = True
                        elif next_val.type == TokenType.NUMBER:
                            # No convertimos si parece fecha ISO (aunque aquí ya fue tokenizado antes)
                            if not re.match(r'\d{4}-\d{2}-\d{2}', next_val.value):
                                next_val.type = TokenType.STRING
                                next_val.value = f'"{next_val.value}"'
                                next_val.raw_value = next_val.value
                                changed = True

                    # 2. Si la clave sugiere NUMBER y el valor es BareWord
                    elif self.NUMBER_HINTS.search(key_name):
                        if next_val.type == TokenType.BARE_WORD:
                            if next_val.value.isdigit():
                                next_val.type = TokenType.NUMBER
                                next_val.raw_value = next_val.value
                                changed = True

            i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)