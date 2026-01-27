from typing import List, Type
from pyparsejson.rules.base import Rule
from pyparsejson.rules.registry import RuleRegistry

class RuleSelector:
    def __init__(self):
        self.tags: List[str] = []
        self.explicit_rules: List[Type[Rule]] = []
        self.exclude: List[Type[Rule]] = []

    def add_tags(self, *tags: str):
        self.tags.extend(tags)
        return self

    def add_rules(self, *rules: Type[Rule]):
        self.explicit_rules.extend(rules)
        return self

    def exclude_rules(self, *rules: Type[Rule]):
        self.exclude.extend(rules)
        return self

    def resolve(self) -> List[Type[Rule]]:
        rules = set()

        for tag in self.tags:
            rules.update(RuleRegistry.get_rules(tag))

        rules.update(self.explicit_rules)
        rules.difference_update(self.exclude)

        return sorted(
            rules,
            key=lambda r: r.priority
        )
