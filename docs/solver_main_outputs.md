# solver_main.py 실행 시 물리적으로 생성되는 파일

`solver_main.py`를 실행하면 아래 위치에 파일이 생성됩니다.

---

## 1. memory/ (ARCKG 비교 결과)

`compare(comp1, comp2, save=True)` 호출 시 `id_pair_to_comparison_path` 규칙에 따라 저장됩니다.

| 비교 단계 | 저장 경로 예시 (root = `memory/`) |
|-----------|-----------------------------------|
| GRID      | `TASK_nodes/TASK_{hex}/PAIR_nodes/PAIR_{n}/GRID_edges/GRID/{score}/GRID_{g1}-GRID_{g2}.json` |
| OBJECT    | `TASK_nodes/.../GRID_edges/OBJECT/{score}/OBJECT_{o1}-OBJECT_{o2}.json` |
| PIXEL     | `TASK_nodes/.../GRID_edges/PIXEL/{score}/PIXEL_{p1}-PIXEL_{p2}.json` |
| PAIR      | `TASK_nodes/TASK_{hex}/PAIR_edges/PAIR/{score}/PAIR_{n1}-PAIR_{n2}.json` |

- **호출 위치**: `workers/arc_solver.py` — GRID/OBJECT/PIXEL 단계에서 `compare(..., save=True)` 여러 번 호출.

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

- **memory/TASK_nodes/**, **PAIR_nodes/**, **GRID_nodes/**, **OBJECT_nodes/**, **PIXEL_nodes/**  
  - ARCKG 컴포넌트의 `.save()`가 호출될 때만 생성. 현재 solver_main → test() 흐름에서는 호출되지 않음.
- **프로젝트 루트의 `comparison_result_*_grid.json`**  
  - `ARCKG/comparison.py` 또는 `program_gen/rules.py`의 `if __name__ == "__main__"` 블록을 직접 실행했을 때만 생성됨. solver_main에서는 생성되지 않음.

---

요약: **solver_main.py** 실행 시 실제로 생성되는 것은 **(1) memory/ 아래 비교 결과 JSON**과 **(2) outputs/generated_codes/ 아래 .py 및 ast/** 입니다.
