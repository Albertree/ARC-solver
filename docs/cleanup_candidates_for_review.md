# 삭제 후보 검사 결과 (solver_main.py 기준)

**기준**: `solver_main.py` 실행에 필요한 것 + **DSL 전부 유지**.  
나머지 중 사용처가 없거나, 다른 진입점(main.py 등) 전용인 항목만 삭제 후보로 분류했습니다.

---

## 1. solver_main.py 의존 관계 (유지 대상)

```
solver_main.py
  → managers.arc_manager (ARCManager)
  → workers.arc_solver (ARCSolver)
  → basics.utils (printcg)

arc_solver.py
  → comparison, make_rule, program (ProgramManager), DSL.*, basics.utils, ARCKG(간접)

program.py
  → ARCKG (task, grid, tf_grid), comparison, make_rule, DSL (apply, transformation, util, selection)

arc_manager.py
  → ARCKG.task, data/ 경로 사용
```

**반드시 유지**:  
`solver_main.py`, `managers/`, `workers/arc_solver.py`, `program.py`, `comparison.py`, `make_rule.py`, `ARCKG/`, `DSL/`, `DSL_activation_rule/`, `basics/utils.py`(및 `basics/__init__.py`), `data/`, 설정 파일(`pyproject.toml`, `pyrightconfig.json` 등)

---

## 2. 삭제해도 되는 후보 (검토용)

### 2.1 다른 진입점 / 구버전 (삭제 권장)

| 항목 | 이유 |
|------|------|
| **main.py** | `CLIManager`, `workers.solver.Solver` 사용. `managers.cli_manager` 없음, `workers.solver`는 삭제된 `components/` 등 참조 → **solver_main과 별개 파이프라인이며 이미 동작 불가** |
| **solver2_main.py** | `solver_main.py`와 거의 동일 (ARCSolver + test()). **중복 진입점** |
| **workers/solver.py** | `main.py` 전용. `components/`, `cli_manager`, `tf_abstractor`, `tf_generator` 등 참조(일부 없음) → **solver_main 경로에서 미사용** |
| **workers/arc_solver_old.py** | arc_solver 구버전. **현재는 arc_solver.py만 사용** |

### 2.2 main.py 전용 모듈 (main 삭제 시 함께 삭제 가능)

| 항목 | 이유 |
|------|------|
| **tools/** (폴더 전체) | `main.py`에서만 `tools.VISUALIZATION.plot_data` 사용. solver_main·program·comparison·make_rule 경로에서는 미사용 |

※ `managers/cli_manager.py`는 현재 프로젝트에 **없음** (main.py가 참조만 하고 있음).

### 2.3 solver_main 경로에서 미사용 파일

| 항목 | 이유 |
|------|------|
| **ARCKG_DSL.py** (루트) | 어느 모듈에서도 import 되지 않음 |
| **DSL_parameter_rule.json** (루트) | 코드에서 참조 없음 |
| **basics/ARCLOADER.py** | solver_main·arc_solver·program에서 미사용 |
| **basics/VISUALIZATION.py** | solver_main·arc_solver·program에서 미사용 |
| **basics/settings.json** | solver_main 경로에서 미사용 (다른 스크립트에서 쓸 수는 있음) |

---

## 3. 유지 권장 (선택/문서)

| 항목 | 비고 |
|------|------|
| **main_program_run_manual.py** | `ProgramManager`로 이미 생성된 프로그램을 수동 실행. solver_main과 **같은 program/데이터** 사용. 지우지 않으면 “생성된 코드 수동 실행”용으로 유지 가능 |
| **docs/** | 문서 유지 권장 |
| **memo.txt**, **memory_structure.txt**, **tree.txt** | 메모/구조 문서. 삭제 여부는 취향 |

---

## 4. 요약: 삭제 목록 제안

**한꺼번에 지우면 폴더가 가벼워지는 것들:**

1. **main.py**
2. **solver2_main.py**
3. **workers/solver.py**
4. **workers/arc_solver_old.py**
5. **tools/** (폴더 전체)
6. **ARCKG_DSL.py**
7. **DSL_parameter_rule.json**
8. **basics/ARCLOADER.py**
9. **basics/VISUALIZATION.py**
10. **basics/settings.json** (선택)

**유지:**  
- **solver_main.py** 및 위 1절 의존 관계 전체  
- **DSL/** 전부, **DSL_activation_rule/** 전부  
- **main_program_run_manual.py** (원하면 나중에만 삭제)

이 목록 그대로 삭제해도 `solver_main.py` 실행에는 영향 없습니다.  
확인 후 “이 목록으로 지워줘”라고 하면 그때 실제 삭제 진행하겠습니다.
