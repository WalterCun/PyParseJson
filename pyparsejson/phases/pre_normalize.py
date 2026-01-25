class PreNormalizeText:
    """
    Limpieza inicial del texto crudo antes de tokenizar.
    """
    def process(self, text: str) -> str:
        if not text:
            return ""
        # Normalización básica de saltos de línea
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        return text.strip()
