# Solver vs 수도코드 비교 및 수정 계획

수도코드(`exploration_hierarchy_pseudocode.md`)와 현재 `ARCSolver.test()` 구현을 비교하고, 수도코드대로 맞추기 위한 수정 계획을 정리한 문서다.

---

## 1. 유사도 요약

| 수도코드 단계 | 현재 solver (`test()`) | 유사도 |
|---------------|------------------------|--------|
| **목적 세우기** (TASK property → PAIR property → 목적) | 없음. `test()`는 곧바로 `for pair in example_pairs` 진입. | ❌ 없음 |
| **그리드 만들기 시도** (GRID property: size, color, contents → 실패 시 내부 탐색) | 없음. 곧바로 `compare(input_grid, output_grid)` 수행. | ❌ 없음 |
| **PAIR 내부 탐색** (GRID → OBJECT → PIXEL 비교) | GRID/OBJECT/PIXEL 단계별 compare + rules + program 생성·저장·실행 있음. | ✅ 유사 |
| **PAIR 간 탐색** (pair_idx ≥ 1일 때 PAIR_component_comparison) | 없음. pair1 처리 후 pair0–pair1 component 비교 호출 없음. | ❌ 없음 |
| **ABSTRACTION** (pair program0 + pair program1 → 추상 프로그램) | `solver_main.py`에서 `solver.test()` **후**에 `save_abstract_program()` 호출. solver 내부에는 없음. | △ 별도 진입점 |

---

## 2. 현재 solver 진입·흐름 (요약)

- **진입**: `solver_main.py` → `ARCSolver(TASK_HEX_CODE)` 생성 → `solver.test()` 호출.
- **test()**:
  - `for pair_idx, pair in enumerate(self.task.example_pairs):`
  - `if len(pair.program) == 0:` 일 때만:
    - GRID: `compare(pair.input_grid, pair.output_grid)`, rules, `generate_program_with_rules`, `save_program(..., "GRID")`, 실행 후 성공 시 continue.
    - 실패 시 OBJECT: `grid_result.objects` vs `pair.output_grid.objects` 비교, rules, program 저장·실행.
    - 실패 시 PIXEL: `object_result.pixels` vs `pair.output_grid.pixels` 비교, program 저장·실행.
  - PAIR 간 비교·추상화는 `test()` 안에 없음.
- **추상화**: `solver_main.py`에서 `test()` 반환 후 `save_abstract_program(task_hex_code, level)`를 GRID/OBJECT/PIXEL마다 호출.

---

## 3. 수도코드대로 수정할 때 계획

### 3.1 목적 세우기 (TASK 수준) — 추가

- **위치**: `test()` **맨 앞**, PAIR 루프 **전**.
- **할 일**:
  1. TASK property 확인.  
     - 이미 `self.task.example_pairs`, `self.task.test_pairs`가 있으므로 `example_pair_count`, `test_pair_count`는 `len(...)`으로 확보 가능.  
     - TASK에 `update_property()`가 있으면 호출해 두고, 없으면 인메모리만 써도 됨.
  2. 각 PAIR(example + test)의 property 확인.  
     - PAIR에는 `grid_count`가 필요. `ARCKG/pair.py`에서 `self.property['grid_count'] = len(self.childs)`.  
     - 현재 PAIR이 `input_grid`, `output_grid`만 노출할 수 있으므로, example pair는 grid_count=2, test pair는 보통 1(입력만 주어짐) 등으로 설정 가능하면 그렇게 읽거나, PAIR에 `update_property()`가 있으면 호출해 `property['grid_count']` 사용.
  3. 목적 설정.  
     - “test pair에 없는 그리드를 생성한다”를 solver 상태에 저장 (예: `self.goal = 'create_missing_grid'`)하거나, 최소한 주석/로그로 “목적: test pair의 output grid 생성” 명시.
- **코드 변경**: `test()` 상단에 `_set_goal_from_task_and_pairs()` 같은 함수 호출 추가. 내부에서 TASK/PAIR property 읽고 `self.goal` 등 설정.

### 3.2 그리드 만들기 시도 (PAIR 루프 안, GRID 비교 전) — 추가

- **위치**: PAIR 루프 안, **`compare(pair.input_grid, pair.output_grid)` 호출 전**.
- **할 일**:
  1. “그리드를 만들기 위해” PAIR 아래 GRID property 탐색.  
     - 목표 output은 `pair.output_grid`. 이걸 “size, color, contents”만으로 만들 수 있는지 시도.
  2. **size**: output_grid의 height, width를 알고 있으면 “size는 결정 가능”으로 두거나, test일 땐 모르므로 “결정 불가”로 둠.  
  3. **color**: output에 쓰인 색 집합은 알 수 있음. “color만으로 grid를 만든다”는 건 보통 불가에 가깝이 두면 됨.  
  4. **contents**: 수도코드대로 “거의 모든 상황에서 만들지 못함”으로 간주하고, 시도하면 실패로 처리.
  5. 하나라도 만들지 못하면 GRID를 직접 만들 수 없다고 보고 → **기존 GRID 내부 탐색**(`compare(input_grid, output_grid)` 이후 OBJECT/PIXEL)으로 진행.
- **코드 변경**:
  - `_try_make_grid_from_property(pair)` 같은 함수 추가.  
    - 입력: `pair` (또는 `pair.output_grid`).  
    - 내부: output_grid.property 또는 size/color/contents에 해당하는 정보만 보고 “직접 생성 가능 여부” 판단 (실제로는 대부분 False 반환).  
  - `test()`에서 GRID 단계 진입 직전에 `if not self._try_make_grid_from_property(pair):` 다음에 기존 `compare(...)` 블록 실행하도록 분기.

### 3.3 PAIR 간 탐색 (PAIR_component_comparison) — 추가

- **위치**: PAIR 루프 안, **pair_idx >= 1**일 때, 해당 pair에 대한 program 저장(GRID 또는 OBJECT/PIXEL 중 마지막으로 저장한 레벨) **직후**.
- **할 일**:
  - pair0와 pair1의 component 비교:  
    `compare(pair0.input_grid, pair1.input_grid, save=True)`,  
    `compare(pair0.output_grid, pair1.output_grid, save=True)`.  
  - 필요하면 OBJECT 단위도 동일한 방식으로 비교.  
  - 비교 결과는 이미 `compare(..., save=True)`로 memory에 저장됨.  
  - (선택) `outputs/generated_codes/{task_hex_code}/{level}/` 아래에 “이번에 비교한 component 쌍” 요약 JSON 저장.
- **코드 변경**:
  - `_compare_pair_components(pair0, pair1)` 함수 추가.  
  - `test()`에서 `pair_idx >= 1`이고, 현재 pair에 대해 program 저장한 직후에 `self._compare_pair_components(self.task.example_pairs[0], pair)` 호출.

### 3.4 추상화 (ABSTRACTION) — 위치 선택

- **현재**: `solver_main.py`에서 `solver.test()` 후에 `save_abstract_program(...)` 호출.
- **수도코드**: “모든 pair 처리 후 또는 pair1 저장 직후 설계에 따라”라고 되어 있음.
- **선택지**:
  - **A**: 지금처럼 `solver_main.py`에서만 호출 (solver는 pair program 생성 + PAIR component 비교까지만 담당).  
  - **B**: `test()` 끝에서 “example pair가 2개 이상이면” `save_abstract_program()`를 solver 내부에서 호출해 추상화까지 한 번에 수행.
- **권장**: 구조를 맞추는 것만 목적이면 **A** 유지해도 됨. “solver = 탐색 + program 생성 + component 비교, main = 오케스트레이션 + 추상화”로 역할 분리 가능.

---

## 4. 수정 순서 제안

1. **목적 세우기** (`_set_goal_from_task_and_pairs()` 추가, `test()` 상단에서 호출) — TASK/PAIR property 읽고 목적 명시.
2. **그리드 만들기 시도** (`_try_make_grid_from_property(pair)` 추가, GRID 비교 전 호출) — 실패 시 기존 GRID 내부 탐색으로 진행.
3. **PAIR 간 탐색** (`_compare_pair_components(pair0, pair1)` 추가, pair_idx ≥ 1일 때 program 저장 직후 호출).
4. **추상화** — 필요 시 solver 내부로 옮기거나, 현재처럼 main에 두고 문서만 맞춤.

---

## 5. 정리

- **이미 비슷한 부분**: PAIR 내부의 GRID → OBJECT → PIXEL 비교·규칙·program 생성·저장·실행.
- **없어서 넣을 부분**: (1) 목적 세우기 루프, (2) 그리드 만들기 시도 루프, (3) pair_idx ≥ 1일 때 PAIR component 비교.
- **선택**: 추상화 호출을 solver 안으로 넣을지는 설계 선택으로 두고, 위 1–3만 적용해도 수도코드의 “전체 흐름”과 대부분 일치하게 만들 수 있다.
