from typing import List, Type, Set
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry


class RuleSelector:
    """
    Constructor (Builder) para seleccionar y filtrar reglas de reparación.
    Permite combinar reglas por tags, añadir reglas específicas y excluir otras.
    """

    def __init__(self):
        self.tags: List[str] = []
        self.explicit_rules: List[Type[Rule]] = []
        self.exclude: List[Type[Rule]] = []

    def add_tags(self, *tags: str) -> 'RuleSelector':
        """Añade reglas asociadas a los tags especificados."""
        self.tags.extend(tags)
        return self

    def add_rules(self, *rules: Type[Rule]) -> 'RuleSelector':
        """Añade clases de reglas específicas explícitamente."""
        self.explicit_rules.extend(rules)
        return self

    def exclude_rules(self, *rules: Type[Rule]) -> 'RuleSelector':
        """Excluye clases de reglas específicas de la selección final."""
        self.exclude.extend(rules)
        return self

    def resolve(self) -> List[Type[Rule]]:
        """
        Resuelve la lista final de clases de reglas, aplicando inclusiones,
        exclusiones y ordenamiento por prioridad.
        """
        rules: Set[Type[Rule]] = set()

        # 1. Recolectar reglas por tags
        for tag in self.tags:
            rules.update(RuleRegistry.get_rules(tag))

        # 2. Añadir reglas explícitas
        rules.update(self.explicit_rules)

        # 3. Aplicar exclusiones
        rules.difference_update(self.exclude)

        # 4. Ordenar por prioridad (menor valor = mayor prioridad)
        return sorted(
            list(rules),
            key=lambda r: r.priority
        )
