"""
Operators: generic names only.
- submit-answer: try to produce and submit an answer (no strategy-specific name).
- set-exploration-target: choose which scope/group to explore (abstract scope, no concrete routine name).
- explore: perform exploration for the current target (implementation detail internal).
Effect dict is applied by WorkingMemory.apply_effect().
"""

from __future__ import annotations

from typing import Any, Callable, NamedTuple

from soar.wm import WorkingMemory


class OperatorSpec(NamedTuple):
    precondition: Callable[[WorkingMemory], bool]
    effect: Callable[[WorkingMemory], dict[str, Any]]


# Abstract exploration scopes (order for progression). No concrete solver method names.
SCOPES_ORDER: list[tuple] = [
    ("INTER_PAIR", "GRID"),   # across pairs at grid level
    ("PAIR", 0, "GRID"),     # within one pair at grid level
    ("PAIR", 0, "OBJECT"),   # within one pair at object level
    ("PAIR", 0, "PIXEL"),    # within one pair at pixel level
]

_KEY_TARGETS_SET = "_targets_set"
_KEY_EXPLORED_SCOPES = "_explored_scopes"


def _has_output_deficit(wm: WorkingMemory) -> bool:
    """True if we need at least one test output."""
    for d in wm.deficits:
        if isinstance(d, (list, tuple)) and len(d) >= 2 and d[1] == "contents":
            return True
        if isinstance(d, dict) and d.get("attribute") == "contents":
            return True
    return False


def _targets_set(wm: WorkingMemory) -> list:
    return list(wm.found.get(_KEY_TARGETS_SET, []))


def _explored_scopes(wm: WorkingMemory) -> list:
    return list(wm.found.get(_KEY_EXPLORED_SCOPES, []))


def _scope_explored(wm: WorkingMemory, scope: tuple) -> bool:
    return scope in _explored_scopes(wm)


# ---------- submit-answer: generic "try to produce and submit an answer" ----------


def cond_submit_answer(wm: WorkingMemory) -> bool:
    """Propose when we need an answer; allow retry after explore (explore clears submit-answer from tried)."""
    return _has_output_deficit(wm) and "submit-answer" not in wm.tried


def effect_submit_answer(wm: WorkingMemory) -> dict[str, Any]:
    """
    Try to produce an answer from current knowledge. No strategy-specific name;
    implementation may use grid-level prediction, program execution, etc.
    """
    task = wm.task or {}
    task_id = task.get("task_id") or ""
    if not task_id:
        return {"add_tried": ["submit-answer"]}
    try:
        import os
        from arc_env.solver_agent import ENV_AGENT_MODE
        from workers.arc_solver import ARCSolver

        os.environ[ENV_AGENT_MODE] = "1"
        solver = ARCSolver(task_id, interactive=False)
        # 16단계 흐름(docs/solver_flow_16_steps.md): TASK/PAIR property → N_T 비교 → N_P·G_0/G_1·P_0 비교 → 프로그램·예측
        use_flow_16 = os.environ.get("USE_FLOW_16", "1") == "1"
        if use_flow_16:
            solver.run_solver_flow_16_steps()
        else:
            solver._compare_grids_across_pairs()
            solver._predict_test_g1()
        predictions = getattr(solver, "_test_output_predictions", None) or []
        n_test = max(1, len(task.get("test", [])))
        add_found: dict[str, Any] = {}
        remove_deficits: list[tuple] = []
        for i in range(min(len(predictions), n_test)):
            pred = predictions[i] if i < len(predictions) else None
            if pred is not None:
                view = getattr(pred, "view", None)
                if view is None and hasattr(pred, "colorgrid"):
                    view = pred.colorgrid
                if view is None and isinstance(pred, (list, tuple)):
                    view = pred
                if view is not None:
                    add_found[f"output_test_{i}"] = view
                    remove_deficits.append(("GRID", "contents", f"output-test-{i}"))
        out: dict[str, Any] = {"add_tried": ["submit-answer"], "add_found": add_found}
        if remove_deficits:
            out["remove_deficits"] = remove_deficits
        return out
    except Exception:
        return {"add_tried": ["submit-answer"]}


# ---------- set-exploration-target: choose which scope to explore (abstract) ----------


def cond_set_exploration_target(wm: WorkingMemory) -> bool:
    """Propose when we need a new target: at TASK (start) or current focus already explored."""
    if not wm.deficits:
        return False
    targets = _targets_set(wm)
    explored = _explored_scopes(wm)
    # Only set next target when we have none (focus is TASK) or current focus is already explored
    if wm.focus == "TASK" and not targets:
        return True
    if wm.focus in explored:
        for scope in SCOPES_ORDER:
            if scope not in targets:
                return True
    return False


def effect_set_exploration_target(wm: WorkingMemory) -> dict[str, Any]:
    """Set focus to the next exploration target (abstract scope)."""
    targets = _targets_set(wm)
    for scope in SCOPES_ORDER:
        if scope not in targets:
            new_targets = targets + [scope]
            return {
                "set_focus": scope,
                "add_found": {_KEY_TARGETS_SET: new_targets},
            }
    return {}


# ---------- explore: perform exploration for current target (implementation internal) ----------


def cond_explore(wm: WorkingMemory) -> bool:
    if not wm.deficits:
        return False
    focus = wm.focus
    if focus == "TASK":
        return False
    if focus not in SCOPES_ORDER:
        return False
    return not _scope_explored(wm, focus)


def _run_exploration_for_scope(task_id: str, scope: tuple) -> None:
    """Run the exploration for the given scope. No concrete names exposed."""
    import os
    from arc_env.solver_agent import ENV_AGENT_MODE
    from workers.arc_solver import ARCSolver

    os.environ[ENV_AGENT_MODE] = "1"
    solver = ARCSolver(task_id, interactive=False)
    if scope == ("INTER_PAIR", "GRID"):
        solver._compare_grids_across_pairs()
    # Other scopes: could run pair-level comparison / program gen here; for now just mark explored
    # e.g. ("PAIR", 0, "GRID") -> solver logic for pair 0 grid level


def effect_explore(wm: WorkingMemory) -> dict[str, Any]:
    """Explore the current target. What that does is an implementation detail."""
    task = wm.task or {}
    task_id = task.get("task_id") or ""
    focus = wm.focus
    explored = _explored_scopes(wm)
    if focus in explored:
        return {}
    if task_id and isinstance(focus, tuple):
        _run_exploration_for_scope(task_id, focus)
    new_explored = explored + [focus]
    return {
        "add_found": {_KEY_EXPLORED_SCOPES: new_explored},
        "add_tried": ["explore"],
        "remove_tried": ["submit-answer"],
    }


# ---------- Registry ----------


OPERATORS: dict[str, OperatorSpec] = {
    "submit-answer": OperatorSpec(cond_submit_answer, effect_submit_answer),
    "set-exploration-target": OperatorSpec(cond_set_exploration_target, effect_set_exploration_target),
    "explore": OperatorSpec(cond_explore, effect_explore),
}


def get_operator(name: str) -> OperatorSpec | None:
    return OPERATORS.get(name)
