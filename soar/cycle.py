"""
Decision cycle: propose -> select -> apply.
Impasse: no operator or select returns None -> set subgoal (optional), then next cycle or stop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from soar.wm import WorkingMemory, STATE_ID
from soar.operators import OPERATORS
from soar.rules import Proposer, default_proposer
from soar.preferences import select_operator


@dataclass
class CycleResult:
    """Result of one or more cycle steps."""
    wm: WorkingMemory
    applied_operator: Optional[str]
    impasse: bool
    steps: int


def run_one_cycle(
    wm: WorkingMemory,
    proposer: Proposer,
    select_fn: Callable[[WorkingMemory, List[str]], Optional[str]],
    operators: Dict[str, Any],
    on_after_apply: Optional[Callable[[WorkingMemory, str], None]] = None,
) -> tuple[WorkingMemory, Optional[str], bool]:
    """
    One cycle: propose -> select -> apply.
    Returns (wm_after, applied_operator_name or None, impasse).
    SOAR 반영: 이전 ^operator 제거, Apply 후 (S1 ^operator op), Impasse 시 (S1 ^impasse no-change).
    """
    wm.clear_operator()
    candidates = proposer.propose(wm)
    selected = select_fn(wm, candidates) if candidates else None
    if selected is None:
        wm.set_impasse("no-change")
        return (wm, None, True)
    spec = operators.get(selected)
    if spec is None:
        wm.set_impasse("no-change")
        return (wm, None, True)
    effect = spec.effect(wm)
    wm.apply_effect(effect)
    wm.set_operator(selected)
    if on_after_apply is not None:
        on_after_apply(wm, selected)
    return (wm, selected, False)


def run_cycle(
    wm: WorkingMemory,
    proposer: Optional[Proposer] = None,
    select_fn: Optional[Callable[[WorkingMemory, List[str]], Optional[str]]] = None,
    operators: Optional[Dict[str, Any]] = None,
    max_steps: int = 100,
    on_impasse: str = "set_subgoal",
    on_after_apply: Optional[Callable[[WorkingMemory, str], None]] = None,
    goal_satisfied: Optional[Callable[[WorkingMemory], bool]] = None,
) -> CycleResult:
    """
    Run propose -> select -> apply until no operator proposed (impasse), max_steps, or goal_satisfied(wm).
    run_one_cycle mutates wm in place when apply is called.
    - on_impasse: "set_subgoal" -> set wm.subgoal and run one more cycle; "stop" -> return with impasse=True.
    - on_after_apply(wm, applied_operator): called after each apply (e.g. to log WM).
    - goal_satisfied(wm): if True, stop early (e.g. all test outputs in wm.found).
    """
    proposer = proposer or default_proposer()
    select_fn = select_fn or select_operator
    operators = operators or OPERATORS

    def _one(wm: WorkingMemory):
        return run_one_cycle(wm, proposer, select_fn, operators, on_after_apply=on_after_apply)

    steps = 0
    last_applied: Optional[str] = None
    while steps < max_steps:
        if goal_satisfied is not None and goal_satisfied(wm):
            return CycleResult(wm=wm, applied_operator=last_applied, impasse=False, steps=steps)
        _, applied, impasse = _one(wm)
        steps += 1
        if applied is not None:
            last_applied = applied
        if impasse:
            if on_impasse == "set_subgoal":
                wm.set_subgoal(("resolve-impasse",))
                _, applied2, impasse2 = _one(wm)
                steps += 1
                if applied2 is not None:
                    last_applied = applied2
                    wm.clear_subgoal()
                    continue
            return CycleResult(wm=wm, applied_operator=last_applied, impasse=True, steps=steps)
    return CycleResult(wm=wm, applied_operator=last_applied, impasse=False, steps=steps)
