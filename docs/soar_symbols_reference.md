# SOAR 심볼 및 기본 함수 레퍼런스

ARC 솔버의 SOAR 스타일 인지 아키텍처에서 사용하는 **심볼(식별자·속성·연산자·Found 키)** 과 **기본 API** 정리.

---

## 1. 구조 요약

- **Working Memory (WM)**: WME 집합. (identifier, attribute, value) 트리플. **읽기**는 propose/select, **쓰기**는 init와 `apply_effect` 시에만.
- **Decision cycle**: propose → select → apply. Impasse 시 subgoal(S2) 한 번 더 시도 후 종료 또는 계속.
- **연산자**: 이름 + precondition(조건) + effect(WM 갱신용 dict). effect는 `WorkingMemory.apply_effect()`로 적용.

---

## 2. WME 식별자 (Identifier)

| 심볼 | 의미 |
|------|------|
| `S1` | 최상위 state (루트). goal, focus, deficits, found, tried 등이 S1에 붙음. |
| `S2` | 첫 번째 subgoal state. Impasse 시 push, 해소 시 pop. (S2 ^superstate S1). |

- 정의 위치: `soar.wm.STATE_ID`, `soar.wm.SUBGOAL_STATE_ID`
- Decision cycle은 **current state**(state stack의 bottom)에서 동작. operator/impasse는 current state에 기록.

---

## 3. WME 속성 (Attribute)

### 3.1 예약 속성 (Reserved)

규칙 매칭/내부용. `wm.found`에서 제외됨.

| 속성 | 설명 |
|------|------|
| `type` | state 타입. S1/S2에 "state". |
| `goal` | 최상위 목표. 예: `("produce-output", task_id)`. |
| `task-id` | 현재 task 식별자 문자열. task 본문은 `wm.task`에 별도 보관. |
| `focus` | 현재 탐색 범위. "TASK" 또는 `("PAIR", i, "GRID")` 등. |
| `deficit` | 결핍 (multi-valued). 값 형태: `(level, attribute, context)` 예: `("GRID", "contents", "output-test-0")`, `("RELATION", 1, ("P0G0","P0G1"))`. |
| `tried` | 시도한 연산자 이름 (multi-valued). |
| `subgoal` | 하위 목표 값. 예: `("resolve-impasse",)`. |
| `operator` | **현재 선택/적용된 연산자** 이름. 사이클마다 clear → apply 후 set. |
| `impasse` | Impasse 유형. "no-change" 등. |
| `superstate` | S2에만. (S2 ^superstate S1). |

### 3.2 사용자/Found 키 (wm.found에 들어가는 이름)

`wm.found`는 예약 속성을 제외한 S1 WME 중 (attr → value) 매핑.

| 패턴/이름 | 설명 |
|-----------|------|
| `output_test_{i}` | i번째 테스트 출력 그리드 (view/colorgrid). |
| `relation_0_{label}` | 0차 관계(단일 컴포넌트 property). 예: relation_0_P0G0. |
| `relation_1_{label1}-{label2}` | 1차 관계(두 컴포넌트 비교 결과). 예: relation_1_P0G0-P0G1. |
| `relation_2_*` | 2차 관계(두 1차 결과 비교). 키 형식: relation_2_... (괄호/공백 제거). |
| `relation_1_*_diff_ordering` | 1/2차 관계에 대한 DIFF 깊이 분석(ordering) 결과. |
| `grid_inv_P{i}_{prop}` | 그리드 불변 결론. prop = size | color | contents, 값 = "unchanged" \| "changed". |
| `_targets_set` | 설정된 탐색 대상 목록 (scope 리스트). |
| `_explored_scopes` | 이미 탐색한 scope 목록. |

---

## 4. 연산자 이름 (Operator Names)

### 4.1 기본 연산자 (soar.operators.OPERATORS)

| 이름 | 역할 |
|------|------|
| `submit-answer` | 현재 지식으로 답 생성 시도 → output_test_i 채우고 deficit 제거. |
| `set-exploration-target` | 다음 탐색 scope 선택 → focus 및 _targets_set 갱신. |
| `explore` | 현재 focus scope에 대한 탐색 수행 → _explored_scopes 갱신, submit-answer 재시도 허용을 위해 remove_tried. |

### 4.2 능동 연산자 (soar.active_operators.ACTIVE_OPERATORS)

| 이름 | 역할 |
|------|------|
| `add-relation-deficits` | 출력 결핍만 있을 때 RELATION 1 결핍 추가 (각 example pair G0 vs G1). |
| `analyze-inside` | 한 컴포넌트(쌍) 내부 분석: 0차 property, 필요 시 1차(G0 vs G1). |
| `analyze-between` | RELATION 1 결핍 하나 해소: 두 컴포넌트 비교 후 relation_1_* 저장. |
| `extract-grid-property-conclusions` | G0 vs G1 비교에서 size/color/contents 결론만 grid_inv_P{i}_* 로 저장. |
| `create-relation-0` | RELATION 0 결핍 하나 해소. |
| `create-relation-1` | RELATION 1 결핍 해소 (analyze-between과 동일 로직). |
| `create-relation-2` | RELATION 2 결핍 해소 (두 1차 결과 비교). |
| `compare-objects-within-grid` | 같은 그리드 내 같은 색 객체 쌍 비교 → relation_1_* 저장. |
| `deepen-diff-ordering` | relation_1_* / relation_2_* 에 대해 DIFF ordering 추출 → *_diff_ordering 저장. |
| `predict-from-invariant` | _diff_ordering 기반 COMM/DIFF 매칭 후 테스트 출력 예측 → output_test_* 채움. |
| `set-exploration-target` | (기본과 동일 이름, merged 시 하나만 유지.) |
| `explore` | (기본과 동일.) |
| `submit-answer` | (기본과 동일.) |

### 4.3 선호도 순서 (Active 에이전트)

`soar.active_agent.PREFERENCE_ORDER_ACTIVE`: 관계 결핍 추가 → 분석(내부/간) → 그리드 결론 추출 → 관계 0/1/2 생성 → 그리드 내 객체 비교 → DIFF 깊이 분석 → invariant 예측 → 탐색 타깃/탐색 → 제출.

---

## 5. Effect 딕셔너리 키 (apply_effect 인자)

연산자 effect는 아래 키들로만 WM을 바꾼다.

| 키 | 값 타입 | 동작 |
|----|---------|------|
| `add_tried` | str 또는 list[str] | 시도한 연산자 이름 추가. |
| `remove_tried` | str 또는 list[str] | 해당 tried 제거. |
| `remove_deficits` | list[tuple] | 해당 deficit WME 제거. |
| `add_deficits` | list[tuple] | deficit WME 추가. |
| `add_found` | dict[str, Any] | (attr, value) 쌍을 S1에 추가. 기존 같은 attr은 제거 후 추가. |
| `set_focus` | Any | focus WME를 해당 값으로 교체. |
| `set_subgoal` | Any | subgoal WME 설정. (S2 push는 WM.set_subgoal()에서 처리.) |
| `clear_subgoal` | bool (키만 있으면 True) | subgoal 제거 및 S2 pop. |

---

## 6. 기본 함수 및 API

### 6.1 Working Memory (soar.wm)

| 함수/메서드 | 설명 |
|-------------|------|
| `WorkingMemory(goal=..., task=..., focus=..., deficits=..., found=..., tried=..., subgoal=...)` | WM 생성. WME로 변환해 저장. |
| `add_wme(id_, attr, value)` | WME 추가 (동일 트리플 중복 방지). |
| `remove_wme(id_, attr, value)` | 일치하는 WME 하나 제거. |
| `remove_wmes_by_attr(id_, attr)` | (id_, attr)인 WME 전부 제거. |
| `get_value(id_, attr)` | 첫 번째 값 또는 None. |
| `get_values(id_, attr)` | 해당 (id_, attr) 값 리스트. |
| `get_all_wmes()` | 전체 WME 스냅샷. |
| `current_state_id()` | state stack bottom (현재 state). |
| `apply_effect(effect)` | 연산자 effect dict 적용. |
| `set_operator(name)` / `clear_operator()` | 현재 state의 ^operator 설정/제거. |
| `set_impasse(type)` / `clear_impasse()` | 현재 state의 ^impasse 설정/제거. |
| `set_subgoal(value)` / `clear_subgoal()` | S2 push/pop 및 관련 WME 갱신. |
| `to_matchable()` | 규칙 매칭용 스냅샷 (goal, focus, deficits, tried, subgoal, found_keys). |
| `copy()` | WM 복사본. |

**Property (읽기 전용):** `goal`, `task`, `focus`, `deficits`, `found`, `tried`, `operator`, `impasse`, `subgoal`.

### 6.2 규칙·제안 (soar.rules)

| 이름 | 설명 |
|------|------|
| `ProductionRule(condition, operator_name)` | condition(wm)이 True일 때 operator_name 제안. |
| `Proposer(rules)` | 규칙 목록 보관. |
| `proposer.propose(wm)` | WM에 맞는 연산자 이름 리스트 반환 (중복 제거). |
| `default_rules_from_operators()` | OPERATORS 기준으로 규칙 목록 생성. |
| `default_proposer()` | 기본 연산자만 쓰는 Proposer. |

### 6.3 선호도 (soar.preferences)

| 이름 | 설명 |
|------|------|
| `PREFERENCE_ORDER` | 기본 연산자 선호 순서 (submit-answer, explore, set-exploration-target). |
| `select_operator(wm, candidates, preference_order=None)` | 후보 중 preference_order에 먼저 나오는 것 선택. 없으면 candidates[0]. None 가능. |

### 6.4 사이클 (soar.cycle)

| 이름 | 설명 |
|------|------|
| `run_one_cycle(wm, proposer, select_fn, operators, on_after_apply=None)` | 한 번: clear_operator → propose → select → apply → set_operator. 반환 (wm, applied_name, impasse). |
| `run_cycle(wm, proposer=..., select_fn=..., operators=..., max_steps=100, on_impasse="set_subgoal", on_after_apply=..., goal_satisfied=...)` | goal_satisfied 또는 max_steps까지 반복. Impasse 시 on_impasse에 따라 subgoal 한 번 더 시도 또는 종료. |
| `CycleResult` | wm, applied_operator, impasse, steps. |

### 6.5 연산자 스펙 (soar.operators / active_operators)

| 이름 | 설명 |
|------|------|
| `OperatorSpec(precondition, effect)` | precondition(wm) -> bool, effect(wm) -> dict. |
| `OPERATORS` | 기본 연산자 dict. |
| `ACTIVE_OPERATORS` | 능동 연산자 dict (active_operators). |
| `merged_operators()` | OPERATORS | ACTIVE_OPERATORS. |
| `get_operator(name)` | 이름으로 OperatorSpec 조회. |

### 6.6 에이전트 공통 (soar.agent_common)

| 이름 | 설명 |
|------|------|
| `build_wm_from_task(task)` | task dict로 WM 초기 상태 구성 (출력 결핍 등). |
| `goal_satisfied(wm)` | 모든 output_test_i가 wm.found에 있으면 True. |
| `answers_from_wm(wm)` | output_test_0, output_test_1, ... 순서의 답 리스트. |

### 6.7 에이전트 (soar.active_agent)

| 이름 | 설명 |
|------|------|
| `active_proposer()` | merged 연산자 기준 Proposer. |
| `select_operator_active(wm, candidates, preference_order=None)` | PREFERENCE_ORDER_ACTIVE로 선택. |
| `ActiveSoarAgent(verbose=..., max_steps=..., use_solver_fallback=...)` | solve(task) → run_cycle + WM.found 기반 답, 부족분은 SolverAgent로 보완. |

---

## 7. Deficit 값 형식

| level | attribute | context 예시 |
|-------|-----------|--------------|
| GRID | contents | "output-test-0", "output-test-1", ... |
| RELATION | 0 | (label,) 예: ("P0G0",) |
| RELATION | 1 | (label1, label2) 예: ("P0G0", "P0G1") |
| RELATION | 2 | (key1, key2) 두 1차 관계 키. |

---

이 문서는 `soar/`, `run_soar_demo.py`, `run_active_agent.py` 기준으로 정리했으며, 코드 변경 시 함께 갱신하는 것을 권장합니다.
