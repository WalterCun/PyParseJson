class Context:
    """
    Mantiene el estado del proceso de parsing/reparación.
    """
    def __init__(self, text: str):
        self.original_text = text
        self.current_text = text
        self.applied_rules = []
        self.metadata = {}

    def record_rule(self, rule_name: str):
        self.applied_rules.append(rule_name)
