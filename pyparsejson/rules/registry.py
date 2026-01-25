from typing import Dict, Type, List, Optional
from collections import defaultdict

class RuleRegistry:
    _registry: Dict[str, List[Type['Rule']]] = defaultdict(list)

    @classmethod
    def register(cls, tags: List[str] = None, priority: int = 100):
        def decorator(rule_cls):
            rule_cls.priority = priority
            rule_cls.tags = tags or []
            # Registrar bajo cada tag
            for tag in rule_cls.tags:
                cls._registry[tag].append(rule_cls)
            # Registrar bajo 'all'
            cls._registry['all'].append(rule_cls)
            return rule_cls
        return decorator

    @classmethod
    def get_rules(cls, tag: str = 'all') -> List[Type['Rule']]:
        rules = cls._registry.get(tag, [])
        return sorted(rules, key=lambda r: r.priority)
