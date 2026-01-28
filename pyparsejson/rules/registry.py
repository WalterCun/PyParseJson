from typing import Dict, Type, List
from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyparsejson.rules.base import Rule


class RuleRegistry:
    """
    Registro centralizado de reglas de reparación.
    Permite registrar reglas mediante decoradores y recuperarlas por tags.
    """
    _registry: Dict[str, List[Type['Rule']]] = defaultdict(list)

    @classmethod
    def register(cls, tags: List[str] = None, priority: int = 100):
        """
        Decorador para registrar una clase de regla.

        Args:
            tags: Lista de etiquetas para categorizar la regla (ej: 'structure', 'values').
            priority: Prioridad de ejecución (menor valor = se ejecuta antes).
        """
        def decorator(rule_cls):
            rule_cls.priority = priority
            rule_cls.tags = tags or []
            
            # Registrar bajo cada tag específico
            for tag in rule_cls.tags:
                cls._registry[tag].append(rule_cls)
            
            # Registrar siempre bajo 'all'
            cls._registry['all'].append(rule_cls)
            
            return rule_cls
        return decorator

    @classmethod
    def get_rules(cls, tag: str = 'all') -> List[Type['Rule']]:
        """
        Recupera todas las reglas asociadas a un tag, ordenadas por prioridad.
        """
        rules = cls._registry.get(tag, [])
        return sorted(rules, key=lambda r: r.priority)
