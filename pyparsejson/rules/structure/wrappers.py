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

        # Contar colones para heurísticas
        # CASO 16: Contamos también ASSIGN (=) como separador válido para detectar root implícito
        separator_count = sum(1 for t in tokens if t.type in (TokenType.COLON, TokenType.ASSIGN))
        if separator_count == 0:
            return False

        # Si empieza como clave (key: ... o key=...)
        starts_with_key = (tokens[0].type in (TokenType.BARE_WORD, TokenType.STRING) and
                           tokens[1].type in (TokenType.COLON, TokenType.ASSIGN))

        # Si hay estructura ({ o [) en cualquier parte
        has_structure = any(t.type in (TokenType.LBRACE, TokenType.LBRACKET) for t in tokens)

        # Si tiene estructura interna (ej: profile: { ... }), 
        # SOLO aplicamos si empieza explícitamente como una propiedad (key: ...).
        # Esto permite capturar el Caso 15 (múltiples props con objetos anidados)
        # pero evita capturar texto libre mezclado con JSON si no empieza como JSON.
        if has_structure and not starts_with_key:
            return False

        return True

    def apply(self, context: Context):
        tokens = context.tokens

        # CASO 10 & 11: Manejar patrón explícito key: { ... } o key: [ ... ]
        # (Mantenemos esta lógica específica por seguridad y precedencia)
        if len(tokens) >= 3:
            if (tokens[0].type in (TokenType.BARE_WORD, TokenType.STRING) and
                    tokens[1].type in (TokenType.COLON, TokenType.ASSIGN) and
                    tokens[2].type in (TokenType.LBRACE, TokenType.LBRACKET)):
                l_brace = Token(TokenType.LBRACE, "{", "{", tokens[0].position)
                r_brace = Token(TokenType.RBRACE, "}", "}", len(tokens))
                context.tokens = [l_brace] + tokens + [r_brace]
                context.mark_changed()
                context.record_rule(self.name)
                return

        # CASO 16: Usar separator_count que incluye ASSIGN
        separator_count = sum(1 for t in tokens if t.type in (TokenType.COLON, TokenType.ASSIGN))
        starts_with_key = (len(tokens) >= 2 and
                           tokens[0].type in (TokenType.BARE_WORD, TokenType.STRING) and
                           tokens[1].type in (TokenType.COLON, TokenType.ASSIGN))

        # Decidir si envolver
        should_wrap = False

        # Caso simple: un solo par key: val sin estructura compleja
        if separator_count == 1 and not any(t.type == TokenType.LBRACE for t in tokens):
            should_wrap = True

        # Caso múltiple: key: val, key: val...
        elif separator_count >= 2:
            # Si no hay llaves, es seguro envolver (lista plana de propiedades)
            if not any(t.type == TokenType.LBRACE for t in tokens):
                should_wrap = True
            # Si hay llaves (objetos anidados), SOLO envolvemos si empieza como propiedad
            # Esto cubre el Caso 15: id: 1, profile: { ... }
            elif starts_with_key:
                should_wrap = True

        if should_wrap:
            l_brace = Token(TokenType.LBRACE, "{", "{", tokens[0].position)
            r_brace = Token(TokenType.RBRACE, "}", "}", len(tokens))
            context.tokens = [l_brace] + tokens + [r_brace]
            context.mark_changed()
            context.record_rule(self.name)


# -----------------------------------------------------------------
# REGLA: ImplicitArrayRule (NUEVA)
# -----------------------------------------------------------------
@RuleRegistry.register(tags=["structure", "repair"], priority=50)
class ImplicitArrayRule(Rule):
    """
    Detecta arrays implícitos cuando múltiples valores escalares aparecen después de una clave sin corchetes.
    Ejemplo: ids: 1, 2, 3, 4, 5 -> ids: [1, 2, 3, 4, 5]
    """

    def applies(self, context: Context) -> bool:
        # Optimización rápida: debe haber comas y dos puntos
        tokens = context.tokens
        has_comma = any(t.type == TokenType.COMMA for t in tokens)
        has_colon = any(t.type == TokenType.COLON for t in tokens)
        return has_comma and has_colon

    def apply(self, context: Context):
        tokens = context.tokens
        changes = []  # Lista de tuplas (start_index, end_index) para envolver

        i = 0
        while i < len(tokens):
            t = tokens[i]

            # Buscamos patrón: KEY : VALUE , VALUE ...
            if t.type == TokenType.COLON:
                # Verificar que hay un valor después del colon
                if i + 1 >= len(tokens):
                    i += 1
                    continue

                val_start_idx = i + 1
                first_val = tokens[val_start_idx]

                # El primer valor debe ser escalar
                if first_val.type not in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.NULL):
                    i += 1
                    continue

                # Escanear hacia adelante buscando más valores separados por comas
                current_idx = val_start_idx
                values_count = 1
                last_val_end_idx = current_idx

                scan_idx = current_idx + 1

                while scan_idx < len(tokens):
                    # Esperamos una coma
                    if tokens[scan_idx].type != TokenType.COMMA:
                        break

                    # Verificar qué hay después de la coma
                    if scan_idx + 1 >= len(tokens):
                        break

                    next_val = tokens[scan_idx + 1]

                    # Verificar si el siguiente token es el inicio de una nueva clave
                    # Si es BARE_WORD o STRING seguido de COLON, es una nueva clave.
                    is_new_key = False
                    if scan_idx + 2 < len(tokens):
                        if tokens[scan_idx + 2].type == TokenType.COLON:
                            is_new_key = True

                    if is_new_key:
                        break

                    # Verificar si es un valor escalar
                    if next_val.type not in (TokenType.NUMBER, TokenType.STRING, TokenType.BOOLEAN, TokenType.NULL):
                        break

                    # Es un valor válido para el array
                    values_count += 1
                    last_val_end_idx = scan_idx + 1
                    scan_idx += 2  # Avanzar coma y valor

                if values_count >= 2:
                    # Encontramos múltiples valores escalares, agruparlos
                    changes.append((val_start_idx, last_val_end_idx))
                    # Avanzamos el índice principal hasta el final de este grupo
                    i = last_val_end_idx
                else:
                    i += 1
            else:
                i += 1

        # Aplicar cambios en orden inverso para no afectar los índices
        if changes:
            for start, end in reversed(changes):
                # Insertar ]
                ref_token_end = tokens[end]
                r_bracket = Token(
                    type=TokenType.RBRACKET,
                    value="]",
                    raw_value="]",
                    position=ref_token_end.position,
                    line=ref_token_end.line,
                    column=ref_token_end.column
                )
                tokens.insert(end + 1, r_bracket)

                # Insertar [
                ref_token_start = tokens[start]
                l_bracket = Token(
                    type=TokenType.LBRACKET,
                    value="[",
                    raw_value="[",
                    position=ref_token_start.position,
                    line=ref_token_start.line,
                    column=ref_token_start.column
                )
                tokens.insert(start, l_bracket)

            context.tokens = tokens
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