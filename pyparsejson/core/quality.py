from typing import List, Tuple
from pyparsejson.core.context import Context
from pyparsejson.core.token import TokenType, Token

class RepairQualityEvaluator:
    """
    Evalúa la calidad estructural y sintáctica del estado actual de los tokens.
    """

    def evaluate(self, context: Context) -> Tuple[float, List[str]]:
        """
        Retorna un score (0.0 - 1.0) y una lista de problemas detectados.
        """
        issues = []
        tokens = context.tokens
        
        if not tokens:
            return 0.0, ["Empty input"]

        # 1. Balance de Estructuras
        balance_score = self._check_balance(tokens, issues)
        
        # 2. Tokens Inválidos o Peligrosos
        token_score = self._check_tokens(tokens, issues)
        
        # 3. Estructura Sintáctica Básica (adyacencia ilegal)
        syntax_score = self._check_syntax(tokens, issues)

        # Peso de cada componente
        final_score = (balance_score * 0.4) + (token_score * 0.3) + (syntax_score * 0.3)
        
        return round(final_score, 2), issues

    def _check_balance(self, tokens: List[Token], issues: List[str]) -> float:
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
        
        errors += len(stack) # Abiertos sin cerrar
        
        if errors > 0:
            issues.append(f"Unbalanced structure: {errors} errors")
            # Penalización exponencial inversa
            return max(0.0, 1.0 - (errors * 0.1))
        return 1.0

    def _check_tokens(self, tokens: List[Token], issues: List[str]) -> float:
        bad_tokens = 0
        total = len(tokens)
        
        for t in tokens:
            if t.type == TokenType.UNKNOWN:
                bad_tokens += 1
            elif t.type == TokenType.STRING:
                # Detectar strings mal formados o con comillas dobles internas
                val = t.value
                if val.count('"') > 2: # Ej: ""key""
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
        # Detectar patrones ilegales como VALUE VALUE sin coma
        syntax_errors = 0
        
        value_types = (TokenType.STRING, TokenType.NUMBER, TokenType.BOOLEAN, TokenType.NULL, TokenType.BARE_WORD)
        
        for i in range(len(tokens) - 1):
            curr = tokens[i]
            next_t = tokens[i+1]
            
            # Dos valores seguidos sin separador
            if curr.type in value_types and next_t.type in value_types:
                syntax_errors += 1
            
            # Coma seguida de cierre
            if curr.type == TokenType.COMMA and next_t.type in (TokenType.RBRACE, TokenType.RBRACKET):
                syntax_errors += 1

        if syntax_errors > 0:
            issues.append(f"Syntax adjacency errors: {syntax_errors}")
            return max(0.0, 1.0 - (syntax_errors * 0.05))
        return 1.0
