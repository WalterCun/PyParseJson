class PreNormalizeText:
    """
    Fase inicial de limpieza del texto crudo antes de la tokenización.
    Se encarga de estandarizar saltos de línea y eliminar espacios superfluos en los extremos.
    """
    
    @staticmethod
    def process(text: str) -> str:
        """
        Normaliza el texto de entrada.
        """
        if not text:
            return ""
        
        # Normalización básica de saltos de línea a formato Unix (\n)
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        return text.strip()
