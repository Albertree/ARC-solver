# ARCKG — Claude Code Context

This file is the single source of truth for this codebase.
Read this before anything. Do NOT use docs/ for architecture decisions — it contains
past design notes that may be outdated or mismatched with current code.

---

## What This Project Is

ARCKG (ARC Knowledge Graph) is a pure symbolic AI system that solves ARC
(Abstraction and Reasoning Corpus) tasks by building a hierarchical knowledge graph
and running a SOAR-inspired cognitive architecture over it.

Core philosophy:
- Pure symbolic representation — no neural components in the knowledge layer
- Knowledge is stored as *relations* (why), not programs (how)
- Failure (impasse) is informative: it reveals what knowledge is missing
- Anti-unification over relational structure generalizes across tasks

---

## Entry Point

```bash
python main.py
```

`main.py` 하나로 전체 실행. ARCEnvironment + Agent 루프가 여기서 시작.

---

## Data

`data/` 폴더는 기존 레포에서 심볼릭 링크로 연결. 복사하지 않는다.

```bash
ln -s ../ARC-solver/data ./data
```

- `data/` 는 read-only. 절대 수정하지 마.
- 경로 변경 시 이 파일과 `env/arc_environment.py`만 수정.

---

## Module Map

```
arckg_project/
│
├── main.py                     ← 단일 진입점
│
├── ARCKG/                      ← Knowledge Graph core
│   ├── task.py                 TASK node
│   ├── pair.py                 PAIR node
│   ├── grid.py                 GRID node
│   ├── object.py               OBJECT node
│   ├── pixel.py                PIXEL node
│   ├── tf_grid.py              Transformed grid (intermediate execution result)
│   ├── comparison.py           compare() — core relation-building function
│   └── memory_paths.py         Path helpers: id_to_json_path, id_pair_to_comparison_path
│
├── program/                    ← Program generation package
│   ├── __init__.py             Exports: ProgramManager, get_matching_actions
│   ├── rules.py                get_matching_actions() — comparison result → DSL actions
│   ├── manager.py              ProgramManager — generate / save / execute programs
│   └── anti_unification.py     Anti-unify pair programs → abstract task-level program
│
├── managers/
│   └── arc_manager.py          ARCManager — loads task from data/, builds ARCKG structure
│
├── workers/
│   └── arc_solver.py           ARCSolver — GRID/OBJECT/PIXEL solve loop per pair
│
├── env/
│   ├── arc_environment.py      ARCEnvironment — task provision, scoring, time budget, trace
│   └── solver_agent.py         SolverAgent — wraps ARCSolver as env-compatible agent
│
├── agent/                      ← SOAR cognitive architecture (complete)
│   ├── wm.py                   WorkingMemory — WME triples, S1/S2 state stack
│   ├── operators.py            Basic operators: submit-answer, explore, set-exploration-target
│   ├── active_operators.py     Active operators: analyze-inside, analyze-between, etc.
│   ├── cycle.py                run_cycle() — propose → select → apply loop
│   ├── rules.py                ProductionRule, Proposer
│   ├── preferences.py          select_operator(), PREFERENCE_ORDER
│   ├── agent_common.py         build_wm_from_task(), goal_satisfied(), answers_from_wm()
│   └── active_agent.py         ActiveSoarAgent
│
├── memory_system/              ← Memory system (design target, partially implemented)
│   └── working.py              WorkingMemory class (RAM only, no disk)
│
├── basics/
│   └── utils.py                Manual grid visualization, object comparison inspection,
│                               manual object verification, and misc helpers
│
├── data/                       ← symlink → ../ARC-solver/data (read-only)
│
├── semantic_memory/            ← STORAGE: ARCKG node property + comparison edges (no code)
│   └── N_T{hex}/
│       └── E_*.json
│
├── procedural_memory/          ← STORAGE: programs (no code)
│   ├── DSL/                    Domain-Specific Language functions
│   │   ├── apply.py            apply_DSL() dispatcher
│   │   ├── transformation.py   Grid/object transformation functions
│   │   ├── util.py             Helper DSL functions
│   │   └── selection.py        find_object(input_grid, [conditions])
│   └── DSL_activation_rule/    Rule trigger files (JSON)
│       ├── GRID_*.json
│       ├── OBJECT_*.json
│       └── PIXEL_*.json
│
└── episodic_memory/            ← STORAGE: per-task solve episodes (no code)
```

### Dead code — do not touch or reference

`main.py`, `solver2_main.py`, `workers/solver.py`, `workers/arc_solver_old.py`, `tools/`
These are unused remnants. `main.py` references modules that no longer exist.

---

## Knowledge Graph Architecture

### Five-Layer Hierarchy

```
TASK  (T)
 └── PAIR  (P)
      └── GRID  (G)
           └── OBJECT  (O)
                └── PIXEL  (X)
```

**Dependency rule**: upper layers may reference lower layers. Reverse is forbidden.

### Node = Folder, Edge = JSON file

- Every node is a folder with prefix `N_`
- Every edge is a `.json` file with prefix `E_`
- Inclusion (parent → child) is expressed by folder nesting — no separate file

### Three edge types

| Type | File pattern | Meaning |
|------|-------------|---------|
| Property (0th order) | `E_{nodename}.json` | Self-description of a single node |
| Relation (1st order) | `E_{comp1}-{comp2}.json` | Comparison between two nodes |
| Higher-order | `E_(E_{...})-(E_{...}).json` | Comparison between two relation results |

### Relation orders

```
0th = node property (self)
1st = compare(node_A.property, node_B.property)
2nd = compare(1st_relation, 1st_relation)
Nth = compare((N-1)th, (N-1)th)
```

Compound edge inputs are wrapped in `()` in the filename:
```
E_(E_P0G0X6-P0G0X7)-(E_P1G0X8-P1G0X9).json   ← 2nd order
```

### Relation result format

```json
{
  "result": {
    "type": "COMM | DIFF",
    "score": "n/total",
    "category": { ... }
  }
}
```

At scalar leaf: `comp1` and `comp2` are added.
For 2nd+ order: `type`, `score`, `category` are compared independently (even if score
looks redundant — category structure can differ with the same score).

### LCA storage rule

A relation edge is always stored at the **Lowest Common Ancestor (LCA)** node folder
of all entities involved. This applies at every relation order.

Examples:
- Two GRIDs in same PAIR → stored in PAIR folder
- Two PAIR-level edges across pairs → stored in TASK folder

### Node ID format

```
T{hex}.P{p}.G{g}.O{o}.X{x}   (only as deep as needed)
```

Test pairs use letters: `Pa`, `Pb`, ...

---

## Solver Flow

### main.py

```
ARCEnvironment 초기화
Agent 초기화
env.run_benchmark(agent) 실행
```

### ARCSolver.test() — per example pair

```
FOR pair_idx, pair in enumerate(example_pairs):
  IF pair already has program: skip

  ── [Goal setting] ── (MISSING — to be added)
     Read TASK/PAIR properties → set goal: "generate test pair output grid"

  ── [Grid-make attempt] ── (MISSING — to be added)
     Try to construct output_grid from GRID property alone (size / color / contents)
     → Almost always fails at contents → fall through to comparison

  ── [GRID level] ──
     compare(pair.input_grid, pair.output_grid, save=True)  → E_G0-G1.json
     rules = get_matching_actions(comparison_result)
     program = generate_program_with_rules(pair, pair_idx, rules)
     save_program(..., "GRID")
     grid_result = execute_saved_program(..., "GRID")
     IF grid_result == output_grid: continue

  ── [OBJECT level] ── (if GRID fails)
     FOR obj_i in grid_result.objects:
       FOR obj_o in pair.output_grid.objects:
         compare(obj_i, obj_o, save=True)
     all_object_actions = get_matching_actions per comparison
     program = generate_program(base=grid_program, extra=object_actions)
     save_program(..., "OBJECT") → execute → check

  ── [PIXEL level] ── (if OBJECT fails)
     FOR pix_i in object_result.pixels:
       FOR pix_o in pair.output_grid.pixels:
         compare(pix_i, pix_o, save=True)   ← WARNING: O(n²) file writes
     program = generate_program(base=object_program, extra=pixel_actions)
     save_program(..., "PIXEL") → execute

  ── [PAIR component comparison] ── (MISSING — to be added)
     IF pair_idx >= 1:
       compare(pair0.input_grid,  pair1.input_grid,  save=True)
       compare(pair0.output_grid, pair1.output_grid, save=True)
       → used as alignment auxiliary info during anti-unification
```

**Three known gaps vs. design pseudocode** (see docs/plan_solver_vs_pseudocode.md):
1. Goal-setting before PAIR loop
2. Grid-make attempt before GRID comparison
3. PAIR component comparison after pair_idx >= 1

### Prediction philosophy

There are not multiple independent prediction strategies. The solver collects all
available symbolic knowledge and relations, and when the evidence is sufficient,
it produces a single precise prediction. The approach is:

- Gather relational knowledge about the task (via SOAR operators and comparison)
- When enough evidence is accumulated, derive the test output deterministically
- Program execution (`program/`) is one way to verify or express this prediction —
  it is not a separate prediction method, but a verification mechanism

`_predict_test_g1()` in the current code is a simplified approximation of this.
Its three-step cascade (input match → output invariant → transition) should be
understood as progressively stronger evidence requirements, not separate strategies.

### Anti-unification (program_gen/anti_unification.py)

```
flat pair program
  → program_lines_to_terms()
  → _align_term_lists_dp() using .context.json func names as alignment bonus
  → anti_unify_terms() per aligned pair
  → terms_to_program_lines()
  → abstract program with ?vN generalization variables
```

PAIR component comparison results can optionally be used as additional alignment signal
(same component correspondence → alignment bonus).

---

## Edge Creation Timing

| Edge type | When | Volume |
|-----------|------|--------|
| Property `E_T/P/G/O/X` | At task load (`to_json()`) | ~thousands |
| Comparison `E_*-*` | During solving (`compare(..., save=True)`) | ~tens of thousands |

**Design intent**: comparison edges should be created selectively (only for chosen components).
**Current problem**: PIXEL-level double loop creates comparisons for all pixel pairs → massive
file volume. `compare(..., save=False)` exists for in-memory-only use.

---

## SOAR Architecture (agent/)

### Working Memory structure

- S1 (root state): goal, task-id, focus, deficits, found, tried, operator, impasse
- S2 (subgoal state, pushed on impasse): subgoal, superstate=S1
- `found`: attr → value, holds `output_test_{i}` when answers are ready
- `deficits`: list of `(level, attribute, context)` tuples representing knowledge gaps

### Deficit format

| level | attribute | context example |
|-------|-----------|----------------|
| GRID | contents | "output-test-0" |
| RELATION | 1 | ("P0G0", "P0G1") |
| RELATION | 2 | (key1, key2) |

### Basic operators (soar/operators.py)

- `submit-answer`: try to generate test outputs from current WM
- `set-exploration-target`: choose next scope (e.g. INTER_PAIR GRID)
- `explore`: run exploration for current focus scope

### Active operators (soar/active_operators.py)

- `add-relation-deficits`: add RELATION 1 deficits for each example pair
- `analyze-inside`: 0th order property + optional 1st order for one component
- `analyze-between`: resolve one RELATION 1 deficit (compare two components)
- `extract-grid-property-conclusions`: `grid_inv_P{i}_{size|color|contents}` → "unchanged|changed"
- `create-relation-0/1/2`: resolve relation deficits of each order
- `compare-objects-within-grid`: compare same-color object pairs within a grid
- `deepen-diff-ordering`: extract DIFF ordering → `relation_1_*_diff_ordering`
- `predict-from-invariant`: use diff_ordering to predict test output

### Decision cycle

```
propose(wm) → candidates
select(candidates, preference_order) → one operator
apply operator.effect(wm) → wm updated
repeat until goal_satisfied or max_steps or impasse
```

### ActiveSoarAgent.solve(task)

```
1. build_wm_from_task(task)        → WM with output deficits
2. run_cycle(max_steps=50)         → fills wm.found
3. answers_from_wm(wm)             → [output_test_0, output_test_1, ...]
4. SolverAgent fallback for None   → fill missing outputs
5. return answers                  → immediately submitted (1 submission per solve())
```

Each `solve()` call = 1 submission. Up to 3 submissions per task via `can_retry`.

---

## ARCEnvironment (env/)

```python
env = ARCEnvironment(task_list=[...], time_budget_sec=300)
first_task = env.reset()

while not env._done:
    task = env.get_task()
    if task is None: break
    answer = agent.solve(task)
    reward, next_task, done = env.step(answer)
    agent.update_memory(reward)
```

- `answer`: list of output grids, one per test pair
- `reward`: 1.0 = all test pairs correct (pixel-exact match), 0.0 = any mismatch
- `run_benchmark(agent, n=None)` → `{correct, total, results, trace}`

---

## Memory System Design Target

| Memory | Storage | Write | Read |
|--------|---------|-------|------|
| Semantic | `semantic_memory/` filesystem | Task load + comparison | Query by node/edge ID |
| Episodic | `memory/episodic/` | After each solved pair | Session start |
| Procedural | `memory/procedural/` | On success only | Session start (candidate programs) |
| Working | RAM only, no disk | During solve loop | During solve loop |

**I/O discipline** (to prevent disk bottleneck):
- LTM → WM: one load at session start
- WM → LTM: one write at session end (async/buffered)
- No disk I/O inside the solve loop

**WorkingMemory fields** (`memory_system/working.py`):
```python
task_hex, task, pair_idx, current_goal,
candidate_rules, partial_program, steps, reasons, grid_result
```

---

## Physical Outputs

| Path | Content |
|------|---------|
| `semantic_memory/N_T{hex}/E_*.json` | Property + comparison relation edges |
| `outputs/generated_codes/{hex}/{GRID\|OBJECT\|PIXEL}/{hex}_{pair}_{level}.py` | Pair programs |
| `outputs/generated_codes/{hex}/{GRID\|OBJECT\|PIXEL}/ast/*.json` | Program ASTs |
| `outputs/generated_codes/{hex}/{level}/*.context.json` | Func names, step refs |
| `episodic_memory/{task_hex}/{episode_id}.json` | Solve episode records |

---

## Critical Boundaries

```
PIXEL   → never aggregates across objects
OBJECT  → never holds raw pixel coordinates directly
GRID    → never performs object-level relational reasoning
PAIR    → never stores task-level generalizations
TASK    → never stores pair-specific observations
```

---

## Rules for Claude in This Codebase

1. **Do not reference docs/**. This file is the single truth.
2. **One file per task**. Do not modify multiple files at once unless explicitly asked.
3. **Analysis only when asked**. Do not implement during design/review tasks.
4. **Do not cross layer boundaries**. If an implementation would violate the boundary
   table above, stop and ask.
5. **Impasse is intentional**. Do not simplify or remove impasse handling.
6. **No global state**. All state must be passed explicitly or held in node/graph objects.
7. **INTENT comments are contracts**. Implement exactly what the INTENT says.
8. **compare(..., save=True) is expensive**. Do not add unconditional save=True calls
   without asking — this can produce tens of thousands of files.
9. **`program/` is the canonical import**. Use `from program import ProgramManager,
   get_matching_actions`. Never import from make_rule.py or program.py directly.
10. **Dead code exists and must stay untouched**. main.py, solver2_main.py,
    workers/solver.py, workers/arc_solver_old.py, tools/ — ignore completely.