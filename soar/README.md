# soar — SOAR-style decision cycle

- **WorkingMemory** (`wm.py`): Single state object; only written in `apply_effect()`.
- **Operators** (`operators.py`): Registry `OPERATORS[name] = (precondition, effect)`; effect returns dict for `wm.apply_effect()`.
- **Rules** (`rules.py`): `ProductionRule(condition, operator_name)`; `Proposer(rules).propose(wm)` → list of operator names.
- **Preferences** (`preferences.py`): `select_operator(wm, candidates)` → one name or None (impasse).
- **Cycle** (`cycle.py`): `run_one_cycle(wm, proposer, select_fn, operators)`; `run_cycle(wm, ...)` loops until impasse or max_steps.

## Quick use

```python
from soar import WorkingMemory, run_cycle

wm = WorkingMemory(
    goal=("produce-output", "test-pair-0"),
    task=your_task,
    focus="TASK",
    deficits=[("GRID", "contents", "output-test-0")],
)
result = run_cycle(wm, max_steps=50)
# result.wm, result.applied_operator, result.impasse, result.steps
```

## Wiring to ARC solver

- Build `WorkingMemory` from task + initial deficits (e.g. “need output grid contents”).
- After `run_cycle`, read `result.wm.found`, `result.wm.deficits`, `result.wm.focus` and call existing solver steps (e.g. PaG1, compare, program gen) as needed; or implement those as operators that return effects and run the cycle again.
