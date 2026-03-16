"""
SOAR-style cognitive architecture for ARC solver.
- WorkingMemory: single source of state (goal, focus, deficits, found, tried, subgoal).
- Operators: name + precondition + effect (effect returns dict, WM.apply_effect applies it).
- Rules: condition(wm) -> propose operator name.
- Preferences: select one from proposed list.
- Cycle: propose -> select -> apply; impasse -> set subgoal.
"""

from soar.wm import WorkingMemory
from soar.operators import OPERATORS, get_operator, OperatorSpec
from soar.rules import ProductionRule, Proposer
from soar.preferences import select_operator, PREFERENCE_ORDER
from soar.cycle import run_cycle, CycleResult

__all__ = [
    "WorkingMemory",
    "OPERATORS",
    "get_operator",
    "OperatorSpec",
    "ProductionRule",
    "Proposer",
    "select_operator",
    "PREFERENCE_ORDER",
    "run_cycle",
    "CycleResult",
]
