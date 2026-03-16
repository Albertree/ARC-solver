"""
Production rules: condition(wm) -> propose operator name.
Proposer: holds rules, propose(wm) returns list of proposed operator names.
"""

from __future__ import annotations

from typing import Callable, List

from soar.wm import WorkingMemory
from soar.operators import OPERATORS


class ProductionRule:
    """If condition(wm) is True, propose operator_name."""

    __slots__ = ("condition", "operator_name")

    def __init__(self, condition: Callable[[WorkingMemory], bool], operator_name: str):
        self.condition = condition
        self.operator_name = operator_name

    def matches(self, wm: WorkingMemory) -> bool:
        return self.condition(wm)


class Proposer:
    """Holds a list of production rules; propose(wm) returns proposed operator names (deduped)."""

    def __init__(self, rules: List[ProductionRule] | None = None):
        self.rules = list(rules) if rules else []

    def add_rule(self, rule: ProductionRule) -> None:
        self.rules.append(rule)

    def propose(self, wm: WorkingMemory) -> List[str]:
        """Return list of operator names that are proposed by rules that match WM."""
        proposed = []
        for rule in self.rules:
            if rule.matches(wm):
                proposed.append(rule.operator_name)
        return list(dict.fromkeys(proposed))


def default_rules_from_operators() -> List[ProductionRule]:
    """Build one rule per registered operator using its precondition as condition."""
    rules = []
    for name, spec in OPERATORS.items():
        rules.append(ProductionRule(spec.precondition, name))
    return rules


def default_proposer() -> Proposer:
    """Proposer with one rule per operator (precondition = rule condition)."""
    return Proposer(rules=default_rules_from_operators())
