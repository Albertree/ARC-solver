# 기억이 비어 있는 초기 상태에서의 ARC 문제 해결 순서

기억 저장소(Semantic / Episodic / Procedural / Working)가 모두 비어 있는 상황에서, 한 ARC 태스크를 처음 풀 때 **어떤 순서로 무엇이 일어나고, 어느 규칙을 쓰며, 언제 무엇을 어디에 저장하는지**를 단계별로 정리한다.

---

## 0. 초기 상태 (진입 전)

| 저장소 | 상태 |
|--------|------|
| **Semantic** | 비어 있음 (memory/semantic/ 에 TASK/PAIR/GRID 등 없음) |
| **Episodic** | 비어 있음 |
| **Procedural** | 비어 있음 |
| **Working** | 비어 있음 |

진입: `solver_main.py`에서 `TASK_HEX_CODE` 지정 후 `ARCManager.from_hex_code(TASK_HEX_CODE)` → `ARCSolver(TASK_HEX_CODE).test()` 호출.

---

## 1. 태스크 로드 (데이터 → Working + Semantic 쓰기)

### 1.1 태스크 로드 시작

- **호출**: `ARCManager.from_hex_code(task_hex_code)`
- **규칙/메모리**: 아직 어떤 DSL 규칙도 사용하지 않음. 메모리에서 읽지 않음(기억 비어 있음).
- **동작**:
  - `data/ARC_AGI/training/{task_hex_code}.json` 또는 `evaluation/`, `data/` 순으로 파일 탐색.
  - JSON 로드 후 `TASKInfo` 생성.
  - `TASK.from_json(task_info, task_hex_code)` 호출.

### 1.2 TASK.from_json 내부 (구조 생성 + Semantic 저장)

- **순서**:
  1. `TASK` 인스턴스 생성, `update_property()` 호출.
  2. `raw_data['train']`의 각 example에 대해 `PAIR.from_json(example_pair_info, parent=ttt)` 호출.
  3. `raw_data['test']`의 각 test에 대해 동일하게 `PAIR.from_json(...)` 호출.
  4. `ttt.example_pairs`, `ttt.test_pairs` 설정 후 `ttt.update_property()` 호출.
  5. **`ttt.to_json()` 호출** → **Semantic 저장 1**.

**Semantic 저장 1 (TASK)**  
- **언제**: `TASK.from_json` 마지막에서 `ttt.to_json()` 호출 시.  
- **어디로**: `memory/semantic/TASK_nodes/TASK_{hex_code}/`  
- **무엇을**: `TASK_property/TASK_{hex_code}_property.json` (example_pair_count, test_pair_count 등), `TASK_edges` 디렉터리 생성.

### 1.3 PAIR.from_json 내부 (각 train/test pair마다)

- **순서**:
  1. `PAIR` 인스턴스 생성.
  2. `raw_data['input']`으로 `GRID.from_json(input_grid_info, parent=ppp)` → input_grid 생성.
  3. `raw_data['output']`으로 `GRID.from_json(output_grid_info, parent=ppp)` → output_grid 생성.
  4. `ppp.update_property()` 호출.
  5. **`ppp.to_json()` 호출** → **Semantic 저장 2 (PAIR)**.

**Semantic 저장 2 (PAIR)**  
- **언제**: 각 PAIR 생성 직후 `ppp.to_json()` 호출 시.  
- **어디로**: `memory/semantic/TASK_nodes/TASK_{hex}/PAIR_nodes/PAIR_{id}/`  
- **무엇을**: `PAIR_property/PAIR_{id}_property.json`.

### 1.4 GRID.from_json 내부 (각 input/output grid마다)

- **순서**:
  1. `GRID` 인스턴스 생성.
  2. 각 (row, col)에 대해 `PIXEL.from_json(pixel_info, parent=ggg)` → pixels 리스트 구성.
  3. `find_all_objects(raw_data)`로 객체 추출 후 각 객체에 대해 `OBJECT.from_json(object_info, parent=ggg)` → objects 리스트 구성.
  4. `ggg.update_property()` 호출.
  5. **`ggg.to_json()` 호출** → **Semantic 저장 3 (GRID)**.  
     (코드상 `id > 1`인 GRID는 to_json에서 early return하여 저장 생략.)

**Semantic 저장 3 (GRID)**  
- **언제**: 각 GRID(input/output) 생성 직후 `ggg.to_json()` 호출 시.  
- **어디로**: `memory/semantic/TASK_nodes/TASK_{hex}/PAIR_nodes/PAIR_{id}/GRID_nodes/GRID_{0|1}/`  
- **무엇을**: `GRID_property/GRID_{id}_property.json`, `GRID_edges` 디렉터리(점수별 하위 폴더) 생성.

(OBJECT/PIXEL의 from_json에서도 to_json 호출이 있다면, 그 시점에 Semantic에 OBJECT/PIXEL 노드·엣지가 저장된다. 현재 구조에서는 GRID까지가 풀이 흐름에서 직접 쓰인다.)

### 1.5 Working Memory에 넣는 것 (재설계 후)

- **언제**: 태스크 로드가 끝난 직후, `ARCSolver.test()` 진입 전.
- **무엇을**:  
  - `WorkingMemory.task_hex = task_hex_code`  
  - `WorkingMemory.task = ttt` (로드된 TASK 객체)  
  - `WorkingMemory.pair_idx = None` (아직 pair 선택 전)  
  - 나머지(current_goal, candidate_rules, steps, reasons 등)는 비우거나 기본값.

**이 단계에서의 규칙 사용**: 없음. 데이터만 로드하고 구조만 Semantic에 쓴다.

---

## 2. 풀이 루프 진입: example_pairs 순회

- **호출**: `ARCSolver.test()` → `for pair_idx, pair in enumerate(self.task.example_pairs):`
- **조건**: `if len(pair.program) == 0` → 기억이 비어 있으면 항상 True.  
  즉, **모든 example pair에 대해 “프로그램 없음 → 풀이 시도”**로 들어간다.

---

## 3. PAIR 하나당 처리 (pair_idx = 0부터)

각 pair에 대해 아래 3.1 ~ 3.5가 **GRID → (실패 시) OBJECT → (실패 시) PIXEL** 순서로 진행된다.

### 3.1 Working Memory 갱신 (재설계 후)

- **언제**: 해당 pair 처리 시작 시.
- **어디에**: Working Memory (메모리만, 디스크 없음).
- **무엇을**:  
  - `WorkingMemory.pair_idx = pair_idx`  
  - `WorkingMemory.current_goal = "GRID"`  
  - (재설계 후) Episodic/Procedural 조회 시도 → 비어 있으므로 후보 없음.  
  - `WorkingMemory.candidate_rules = []`, `steps = []`, `reasons = []` 초기화.

---

### 3.2 GRID 레벨 풀이

#### 3.2.1 비교 및 비교 결과 저장

- **호출**: `compare(pair.input_grid, pair.output_grid, save=True)`
- **규칙**: 아직 규칙 적용 전. `compare`는 두 GRID의 `property`를 `compare_nested_json`으로 비교해 차이/점수를 낸다.
- **저장**:
  - **언제**: `save=True`이므로 비교 직후.
  - **어디로**: **Semantic** — `id_pair_to_comparison_path(id1, id2, score)`가 반환하는 경로.  
    예: `memory/semantic/TASK_nodes/TASK_{hex}/PAIR_nodes/PAIR_{pair_idx}/GRID_edges/GRID/{score}/GRID_0-GRID_1.json`
  - **무엇을**: `id1`, `id2`, `result`(비교 결과, 점수 포함)를 담은 JSON.

#### 3.2.2 규칙 매칭 (GRID 레벨)

- **호출**: `rules = get_matching_actions(comparison_result)`
- **사용하는 규칙**:
  - `extract_comparison_level(comparison_result["id1"])` → `"GRID"`.
  - `load_matching_rules("GRID", category_key)` → **DSL_precondition/** 아래 `GRID_*.json` 파일만 로드.  
    예: `GRID_color_add_added_color.json`, `GRID_color_add_removed_color.json`, `GRID_size_make_grid.json` 등.
  - 각 규칙의 `condition`을 `evaluate_rule_condition(rule['condition'], comparison_result, param_combo)`로 평가.
  - 조건을 만족하면 `rule['action']`의 인자를 `process_action_args`로 채워 **actions 리스트**에 넣음.
- **저장**: 이 단계에서는 **저장 없음**. `rules`는 Working Memory(또는 솔버 변수)에만 둠.  
  (재설계 후: `WorkingMemory.candidate_rules = rules`, `WorkingMemory.reasons`에 “어떤 규칙이 어떤 조건으로 선택되었는지” 누적 가능.)

#### 3.2.3 GRID 프로그램 생성 및 저장

- **호출**:  
  - `grid_program = self.program_manager.generate_program_with_rules(pair, pair_idx, rules)`  
  - `self.program_manager.save_program(grid_program, pair_idx, "GRID", self.task_hex_code)`
- **규칙**: 위에서 얻은 `rules`(action 리스트)를 그대로 사용. 각 action은 DSL 함수명과 인자로, `generate_program_with_rules`가 이걸 이용해 `apply_DSL(..., 함수명, 인자)` 형태의 코드 라인을 만든다.
- **저장**:
  - **언제**: `save_program` 호출 시.
  - **어디로 (현재)**: `generated_codes/{task_hex_code}/GRID/{task_hex_code}_{pair_idx}_grid.py`
  - **어디로 (재설계 후)**:  
    - **Procedural**: 성공 시에만(3.2.5에서 판단 후) `memory_system.procedural.store_program(program, preconditions, outcome, episode_id)`로 저장.  
    - 초기 상태에서는 아직 에피소드 ID가 없으므로, 에피소드 기록 후 program_id를 붙여 저장하거나, “풀이 종료 시 한꺼번에” 저장할 수 있음.

#### 3.2.4 GRID 프로그램 실행

- **호출**: `grid_result = self.program_manager.execute_saved_program(pair_idx, "GRID", self.task_hex_code)`
- **규칙**: 생성된 GRID 프로그램(이미 저장된 파일)을 실행. 추가 규칙 사용 없음.
- **저장**: 없음. `grid_result`는 Working Memory(또는 솔버 변수)에만 둠.

#### 3.2.5 GRID 결과 검증

- **조건**: `grid_result.view == pair.output_grid.view`
- **성공 시**:
  - **저장 (재설계 후)**:
    - **Episodic**: `episodic.record(episode)` — 이번 pair의 에피소드: task_hex, pair_idx, 입력/출력 스냅샷, GRID 단계만 수행, 적용한 rules, 생성된 프로그램, 선택 이유(reasons), success=True.
    - **Procedural**: `procedural.store_program(grid_program, preconditions, outcome, episode_id)` — GRID 레벨 프로그램과 메타데이터.
  - **다음**: `continue` → 다음 example pair로.
- **실패 시**: OBJECT 레벨로 진행 (3.3).

---

### 3.3 OBJECT 레벨 풀이 (GRID가 실패했을 때만)

#### 3.3.1 OBJECT 비교 및 저장

- **호출**:  
  - `for obj_i in grid_result.objects: for obj_o in pair.output_grid.objects: compare(obj_i, obj_o, save=True)`  
  - `rules = get_matching_actions(comparison_result)` (각 비교마다), `all_object_actions.extend(rules)`
- **사용하는 규칙**:  
  - `load_matching_rules("OBJECT", category_key)` → **DSL_precondition/** 의 `OBJECT_*.json` (예: `OBJECT_color_coloring.json`).
- **저장**:
  - **Semantic**: 각 (obj_i, obj_o) 비교 결과가 `memory/semantic/.../GRID_edges/OBJECT/{score}/OBJECT_{i}-OBJECT_{j}.json`에 저장됨.

#### 3.3.2 OBJECT 프로그램 생성 및 저장

- **호출**:  
  - `object_program = self.program_manager.generate_program_with_rules(pair, pair_idx, all_object_actions, base_program=grid_program)`  
  - `self.program_manager.save_program(object_program, pair_idx, "OBJECT", self.task_hex_code)`
- **규칙**: GRID 프로그램을 베이스로 두고, OBJECT 규칙에서 나온 actions를 추가한 코드 생성.
- **저장**:  
  - **어디로 (현재)**: `generated_codes/{task_hex_code}/OBJECT/{task_hex_code}_{pair_idx}_object.py`  
  - **어디로 (재설계 후)**: Procedural은 “OBJECT 레벨 성공 시” 기록(3.3.4 성공 시).

#### 3.3.3 OBJECT 프로그램 실행 및 검증

- **호출**: `object_result = self.program_manager.execute_saved_program(pair_idx, "OBJECT", self.task_hex_code)`
- **성공 시**: Episodic/Procedural에 OBJECT 레벨 에피소드/프로그램 기록 후 다음 pair로.
- **실패 시**: PIXEL 레벨로 진행 (3.4).

---

### 3.4 PIXEL 레벨 풀이 (OBJECT도 실패했을 때만)

#### 3.4.1 PIXEL 비교 및 저장

- **호출**:  
  - `for pix_i in object_result.pixels: for pix_o in pair.output_grid.pixels: compare(pix_i, pix_o, save=True)`  
  - `get_matching_actions(comparison_result)` → `all_pixel_actions`
- **사용하는 규칙**:  
  - `load_matching_rules("PIXEL", category_key)` → **DSL_precondition/** 의 `PIXEL_*.json` (예: `PIXEL_color_coloring.json`).
- **저장**:  
  - **Semantic**: 각 (pix_i, pix_o) 비교 결과가 `memory/semantic/.../GRID_edges/PIXEL/{score}/PIXEL_{i}-PIXEL_{j}.json`에 저장됨.

#### 3.4.2 PIXEL 프로그램 생성 및 저장

- **호출**: OBJECT 프로그램을 베이스로 PIXEL actions를 붙여 `generate_program_with_rules(..., all_pixel_actions, base_program=object_program_lines)`, `save_program(..., "PIXEL", ...)`.
- **저장**:  
  - **어디로 (현재)**: `generated_codes/{task_hex_code}/PIXEL/...`  
  - **어디로 (재설계 후)**: PIXEL 레벨 성공 시 Episodic/Procedural에 기록.

#### 3.4.3 PIXEL 실행 및 검증

- 성공 시: 해당 pair에 대한 에피소드/프로그램을 Episodic/Procedural에 기록 후 다음 pair로.
- 실패 시: 그래도 “이 pair는 PIXEL까지 시도했으나 실패”로 에피소드만 기록 가능(success=False).

---

## 4. 풀이 종료 시 (한 pair 처리 끝날 때마다, 재설계 후)

- **Working Memory**: 다음 pair로 넘어가기 전에 초기화하거나, pair_idx/current_goal만 바꿔서 재사용.
- **Episodic 저장**  
  - **언제**: 해당 pair에서 “성공한 레벨” 또는 “마지막 시도한 레벨”이 정해진 직후.  
  - **어디로**: `memory/episodic/by_task/{task_hex_code}/{episode_id}.json`  
  - **무엇을**: task_hex, pair_idx, timestamp, 입력/출력 스냅샷, 적용 단계(GRID/OBJECT/PIXEL), steps(적용한 규칙 순서), 생성된 프로그램(코드 또는 경로), reasons(규칙 선택 이유), success, (선택) program_id.
- **Procedural 저장**  
  - **언제**: GRID/OBJECT/PIXEL 중 **성공한** 레벨에 대해서만.  
  - **어디로**: `memory/procedural/programs/{program_id}.json`  
  - **무엇을**: program_id, task_hex, pair_idx, level, code(또는 경로), preconditions, outcome, source_episode_id.

---

## 5. 요약 표: “언제 무엇을 어디에 저장하는가” (초기 상태)

| 단계 | 사용하는 규칙 | Semantic | Episodic | Procedural | Working |
|------|----------------|----------|----------|------------|---------|
| 태스크 로드 | 없음 | TASK/PAIR/GRID(OBJECT/PIXEL) 노드·엣지 디렉터리 | - | - | task, task_hex 등 |
| GRID 비교 | 없음 | GRID_edges 비교 결과 JSON | - | - | comparison_result, rules |
| GRID 규칙 매칭 | DSL_precondition GRID_*.json | - | - | - | candidate_rules, reasons |
| GRID 프로그램 저장 | (생성 시 사용한 rules) | - | - | (성공 시 나중에) | - |
| GRID 실행/검증 후 | - | - | record(episode) | store_program(성공 시) | steps, 결과 정리 |
| OBJECT 비교/규칙 | DSL_precondition OBJECT_*.json | OBJECT 비교 결과 | - | - | all_object_actions |
| OBJECT 프로그램/실행 | (OBJECT 규칙 기반) | - | record(episode) | store_program(성공 시) | - |
| PIXEL 비교/규칙 | DSL_precondition PIXEL_*.json | PIXEL 비교 결과 | - | - | all_pixel_actions |
| PIXEL 프로그램/실행 | (PIXEL 규칙 기반) | - | record(episode) | store_program(성공 시) | - |

---

## 6. 규칙 파일 위치 및 역할 (참고)

- **위치**: `DSL_precondition/`
- **GRID 레벨**: `GRID_color_add_added_color.json`, `GRID_color_add_removed_color.json`, `GRID_size_make_grid.json` 등 — `get_matching_actions`에서 `comparison_level == "GRID"`일 때 로드.
- **OBJECT 레벨**: `OBJECT_color_coloring.json` 등 — OBJECT 비교 결과에 대해 조건 평가 후 action 생성.
- **PIXEL 레벨**: `PIXEL_color_coloring.json` 등 — PIXEL 비교 결과에 대해 동일.

이 순서와 “언제 무엇을 어디로 저장하는지”를 기준으로, 기억이 비어 있는 초기 상태에서의 한 번의 풀이가 완전히 재현 가능하다.
