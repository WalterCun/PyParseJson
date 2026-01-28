from typing import List, Tuple
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token


class RepairQualityEvaluator:
    """
    Evalúa la calidad estructural y sintáctica del estado actual de los tokens.
    Genera un puntaje de confianza (0.0 a 1.0) y una lista de problemas detectados.
    """

    # Pesos para el cálculo del score final
    WEIGHT_BALANCE = 0.4
    WEIGHT_TOKENS = 0.3
    WEIGHT_SYNTAX = 0.3

    def evaluate(self, context: Context) -> Tuple[float, List[str]]:
        """
        Calcula el score de calidad y detecta problemas potenciales.

        Returns:
            Una tupla (score, lista_de_problemas).
        """
        issues = []
        tokens = context.tokens
        
        if not tokens:
            return 0.0, ["Empty input"]

        balance_score = self._check_balance(tokens, issues)
        token_score = self._check_tokens(tokens, issues)
        syntax_score = self._check_syntax(tokens, issues)

        final_score = (
            (balance_score * self.WEIGHT_BALANCE) +
            (token_score * self.WEIGHT_TOKENS) +
            (syntax_score * self.WEIGHT_SYNTAX)
        )
        
        return round(final_score, 2), issues

    def _check_balance(self, tokens: List[Token], issues: List[str]) -> float:
        """Verifica el balance de llaves y corchetes."""
        stack = []
        errors = 0
        
        for t in tokens:
            if t.type in (TokenType.LBRACE, TokenType.LBRACKET):
                stack.append(t.type)
            elif t.type in (TokenType.RBRACE, TokenType.RBRACKET):
                if not stack:
                    errors += 1
                else:
                    last = stack.pop()
                    if (t.type == TokenType.RBRACE and last != TokenType.LBRACE) or \
                       (t.type == TokenType.RBRACKET and last != TokenType.LBRACKET):
                        errors += 1
        
        errors += len(stack)  # Elementos abiertos sin cerrar
        
        if errors > 0:
            issues.append(f"Unbalanced structure: {errors} errors")
            return max(0.0, 1.0 - (errors * 0.1))
        return 1.0

    def _check_tokens(self, tokens: List[Token], issues: List[str]) -> float:
        """Detecta tokens desconocidos o sospechosos."""
        bad_tokens = 0
        total = len(tokens)
        
        for t in tokens:
            if t.type == TokenType.UNKNOWN:
                bad_tokens += 1
            elif t.type == TokenType.STRING:
                val = t.value
                # Detectar strings mal formados (ej: ""key"")
                if val.count('"') > 2:
                    issues.append(f"Suspicious string format: {val}")
                    bad_tokens += 0.5
                if not (val.startswith('"') and val.endswith('"')):
                     issues.append(f"Unclosed string: {val}")
                     bad_tokens += 1

        if bad_tokens > 0:
            issues.append(f"Invalid/Suspicious tokens: {bad_tokens}")
            return max(0.0, 1.0 - (bad_tokens / total))
        return 1.0

    def _check_syntax(self, tokens: List[Token], issues: List[str]) -> float:
        """Detecta errores de sintaxis básicos como adyacencia ilegal de valores."""
        syntax_errors = 0
        value_types = (TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.BARE_WORD)
        
        for i in range(len(tokens) - 1):
            curr = tokens[i]
            next_t = tokens[i+1]
            
            # Dos valores seguidos sin separador (ej: "key" "value")
            if curr.type in value_types and next_t.type in value_types:
                syntax_errors += 1
            
            # Coma seguida inmediatamente de cierre (trailing comma no estándar)
            # Nota: Aunque algunos parsers lo aceptan, aquí lo penalizamos ligeramente como "issue"
            if curr.type == TokenType.COMMA and next_t.type in (TokenType.RBRACE, TokenType.RBRACKET):
                syntax_errors += 1

        if syntax_errors > 0:
            issues.append(f"Syntax adjacency errors: {syntax_errors}")
            return max(0.0, 1.0 - (syntax_errors * 0.05))
        return 1.0
