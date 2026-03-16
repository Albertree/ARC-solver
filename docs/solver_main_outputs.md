# solver_main.py 실행 시 물리적으로 생성되는 파일

`solver_main.py`를 실행하면 아래 위치에 파일이 생성됩니다.

---

## 1. semantic_memory/ (ARCKG 비교 결과)

**물리적 저장소**: 프로젝트 루트 기준 **`semantic_memory/`** 폴더 아래.  
`compare(comp1, comp2, save=True)` 호출 시 `ARCKG/memory_paths.py`의 `MEMORY_ROOT`(= `semantic_memory/`) 기반 경로로 저장됩니다.

| 비교 종류 | 저장 경로 (root = `semantic_memory/`) |
|-----------|--------------------------------------|
| **PAIR 간 GRID 비교** (label1, label2 사용) | `N_T{hex}/E_{label1}-{label2}.json` 예: `N_Teasy0016/E_P0G0-P1G0.json` |
| GRID-GRID (pair 내부 등, id 기반) | `N_T{hex}/N_P{pair_num}/E_G{g1}-G{g2}.json` |
| OBJECT-OBJECT | `N_T{hex}/N_P{pair_num}/E_O{o1}-O{o2}.json` |
| PIXEL-PIXEL | `N_T{hex}/N_P{pair_num}/E_X{x1}-X{x2}.json` |
| PAIR-PAIR | `N_T{hex}/E_P{p1}-P{p2}.json` |

예: task `easy0016`에서 PAIR 간 GRID 비교 P0G0 vs P1G0 → `semantic_memory/N_Teasy0016/E_P0G0-P1G0.json` (task 노드 바로 아래).

- **호출 위치**: `workers/arc_solver.py` — PAIR 간 GRID 비교, 그리고 GRID/OBJECT/PIXEL 단계에서 `compare(..., save=True)` 호출.
- **로그**: PAIR 간 GRID 비교 시 각 쌍마다 저장 루트가 `semantic_memory/`로 출력됨.

---

## 2. outputs/generated_codes/ (program_gen 생성 코드)

`ProgramManager.save_program()` 호출 시 생성됩니다. 기본 경로는 `outputs/generated_codes`입니다.

| 내용 | 경로 |
|------|------|
| 해결 프로그램(.py) | `outputs/generated_codes/{task_hex_code}/{GRID\|OBJECT\|PIXEL}/{task_hex_code}_{pair_index}_{level}.py` |
| AST(json)         | `outputs/generated_codes/{task_hex_code}/{GRID\|OBJECT\|PIXEL}/ast/{task_hex_code}_{pair_index}_{level}.json` |

- **호출 위치**: `workers/arc_solver.py` — `program_manager.save_program(...)` (GRID/OBJECT/PIXEL 각 단계).

---

## 3. 그 외 (solver_main 경로에서는 미생성)

- **semantic_memory/** 아래 TASK/PAIR/GRID/OBJECT/PIXEL 노드  
  - ARCKG 컴포넌트의 `.save()`가 호출될 때만 생성. 현재 solver_main → test() 흐름에서는 호출되지 않음.
- **프로젝트 루트의 `comparison_result_*_grid.json`**  
  - `ARCKG/comparison.py` 또는 `program_gen/rules.py`의 `if __name__ == "__main__"` 블록을 직접 실행했을 때만 생성됨. solver_main에서는 생성되지 않음.

---

요약: **solver_main.py** 실행 시 실제로 생성되는 것은 **(1) semantic_memory/ 아래 비교 결과 JSON**과 **(2) outputs/generated_codes/ 아래 .py 및 ast/** 입니다.
