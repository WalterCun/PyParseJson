from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry

@RuleRegistry.register(tags=["structure", "normalization"], priority=25)
class MergeCompoundKeysRule(Rule):
    """
    Fusiona claves compuestas por múltiples palabras (BARE_WORD) en una sola clave snake_case.
    
    Estrategia:
    1. Busca secuencias de BARE_WORDs que terminan inmediatamente antes de un COLON (:).
    2. Verifica que la secuencia NO esté precedida por otro COLON (lo que indicaría que es un valor).
    3. Fusiona los tokens en uno solo (ej: "deposito" "fecha" -> "deposito_fecha").
    """

    def applies(self, context: Context) -> bool:
        tokens = context.tokens
        # Optimización: Buscar al menos dos BARE_WORD seguidos
        for i in range(len(tokens) - 1):
            if tokens[i].type == TokenType.BARE_WORD and tokens[i+1].type == TokenType.BARE_WORD:
                return True
        return False

    def apply(self, context: Context):
        tokens = context.tokens
        new_tokens = []
        i = 0
        changed = False

        while i < len(tokens):
            current = tokens[i]
            
            # Detectar inicio de posible secuencia
            if current.type == TokenType.BARE_WORD:
                
                # Verificar el token anterior para evitar fusionar valores con claves
                # Si el anterior es COLON o ASSIGN, entonces 'current' es probablemente un valor.
                prev_is_separator = False
                if len(new_tokens) > 0:
                    if new_tokens[-1].type in (TokenType.COLON, TokenType.ASSIGN):
                        prev_is_separator = True
                
                if prev_is_separator:
                    new_tokens.append(current)
                    i += 1
                    continue

                # Mirar hacia adelante para encontrar la extensión de la secuencia
                j = i + 1
                words = [current]
                valid_sequence = False
                
                while j < len(tokens):
                    t = tokens[j]
                    if t.type == TokenType.BARE_WORD:
                        words.append(t)
                        j += 1
                    elif t.type == TokenType.COLON:
                        # Terminó en COLON, es una clave válida
                        valid_sequence = True
                        break
                    else:
                        # Se rompió la secuencia (ej: coma, número, etc.)
                        break
                
                # Solo fusionar si hay más de una palabra y termina en COLON
                if valid_sequence and len(words) > 1:
                    # Construir nuevo valor
                    merged_value = "_".join(w.value for w in words)
                    
                    new_token = Token(
                        type=TokenType.BARE_WORD,
                        value=merged_value,
                        raw_value=merged_value,
                        position=current.position,
                        line=current.line,
                        column=current.column
                    )
                    new_tokens.append(new_token)
                    changed = True
                    
                    # Saltar los tokens consumidos
                    # i apunta al primero, j apunta al COLON.
                    # Queremos que el bucle principal continúe DESDE el COLON (que no fue consumido)
                    i = j 
                    continue

            new_tokens.append(current)
            i += 1

        if changed:
            context.tokens = new_tokens
            context.mark_changed()
            context.record_rule(self.name)
