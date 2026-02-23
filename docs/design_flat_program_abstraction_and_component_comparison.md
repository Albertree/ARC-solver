# Flat pair program에서 추상화 + pair component 비교

## 요약

- **Pair program은 flat 텍스트**이지만, **이미 추상화 경로가 구현되어 있음** (term 변환 + context 기반 정렬 + anti-unify). 따라서 **program 두 개만 있으면** flat만으로도 추상화는 가능하다.
- **A 방안**: **pair program0 + pair program1 + pair component 비교결과**를 함께 써서 추상화한다. 추상화의 본질적 입력은 **pair program0, pair program1** (둘을 anti-unify); **pair component 비교결과**는 프로그램이 아니라 매칭/대응 정보이므로 이것만으로는 anti-unify 불가 → 정렬·step–component 해석용 **보조 정보**로만 사용.
- **A 방식**(pair1 전용 program 생성 후 pair0와 anti-unify)을 유지하면서, **pair program1 생성 직후에 pair component 비교**를 넣어 “비교 가능한 pair program을 먼저 만든 뒤 비교/추상화”하는 흐름을 설계할 수 있다.
- 추상화 방법이 flat만으로도 있으므로, **굳이 A가 아니어도** B(대응 전제로 program 생성)만 고집할 필요는 없다. 다만 “생성 직후 component 비교”를 넣으면 추상화 품질을 보조할 수 있다.

---

## 0. 추상화 입력 vs 보조 정보 (A 방안에서의 역할)

| 자료 | 역할 |
|------|------|
| **pair program0** | 추상화의 **입력 1**. anti-unify의 한쪽 대상. |
| **pair program1** | 추상화의 **입력 2**. anti-unify의 다른쪽 대상. **이 둘이 있어야** LGG(추상 프로그램)를 구할 수 있음. |
| **pair component 비교결과** | **프로그램이 아님.** "pair0의 어떤 GRID/OBJECT가 pair1의 어떤 것과 대응하는지" 같은 **매칭 정보**만 제공. 따라서 **이것만으로는 추상화(anti-unify) 불가**. A 방안에서는 **보조 정보**로만 사용 → term 정렬 시 같은 component 대응 step끼리 맞추는 데 쓰거나, step–component 해석에 사용. |

즉, **A 방안 = (pair program0 + pair program1)으로 추상화하고, (pair component 비교결과)로 그 과정을 도와주는 것**이다.

---

## 1. Flat pair program에서 추상화하는 방법 (이미 구현됨)

Pair program은 **한 줄씩 나열된 Python 소스**이지만, 다음 파이프라인으로 **구조화된 term**으로 바꾼 뒤 anti-unify한다.

| 단계 | 위치 | 설명 |
|------|------|------|
| Flat → term | `program_gen/anti_unification.py` | `program_lines_to_terms(lines)`로 각 줄을 term으로 파싱 (assign, apply_DSL, return, raw 등). |
| 정렬 | `_align_term_lists_dp` | 두 프로그램의 term 리스트를 DP로 정렬. **같은 구조 + 같은 func**일 때 매칭 보너스. |
| func 정보 | `load_context_for_pairs` + `term_list_to_func_names` | 각 pair의 `.context.json`에서 `steps[].line_ref`의 `func=` 값을 읽어, **같은 func끼리 우선 매칭**하도록 사용. |
| LGG | `anti_unify_terms` | 정렬된 term 쌍마다 anti-unify하여 일반화 변수 `?vN` 도입. |
| term → flat | `terms_to_program_lines` | 추상 term을 다시 실행 가능한 Python 라인으로 복원. |

따라서 **“flat 텍스트만으로는 추상화가 안 된다”가 아니라**,  
**flat → term → context(func)로 정렬 보조 → anti-unify → flat** 이라는 방법이 이미 코드에 있다.  
추가로 `task_hex_code`가 있으면 `expression_subst_from_arckg`로 일반화 변수를 ARCKG 기반 DSL 식으로 채울 수 있다.

---

## 2. Pair program ↔ pair component 연결 (현재와 확장)

- **현재**: program 저장 시 `_write_context`가 **같은 pair 내**에서만 쓰는 정보를 저장한다 (task_hex_code, pair_index, level, steps with line_ref).  
  **Pair0 component vs pair1 component** 비교 결과는 아직 추상화 파이프라인에 넣지 않음.
- **Pair component 비교**란: 예를 들어 pair0의 input_grid vs pair1의 input_grid, pair0의 output_grid vs pair1의 output_grid, 또는 GRID/OBJECT/PIXEL 단위로 “어떤 컴포넌트가 서로 대응하는지”를 비교하는 것.
- **연결 방향**:
  - **Option 1**: Pair1 program **생성·저장 직후**에 “pair0 component vs pair1 component” 비교를 한 번 수행하고, 그 결과를 저장해 둔다.
  - **Option 2**: 저장한 비교 결과를 나중에 anti-unify 단계에서 사용한다.  
    예: “pair0의 step i는 GRID_0, pair1의 step j는 GRID_0을 다룬다” 같은 **step–component 매핑**을 만들어, `_align_term_lists_dp`에 추가 보너스(같은 component 대응 시)로 쓰거나, alignment 후보를 제한하는 데 쓴다.

---

## 3. A + “pair program1 생성 직후 pair component 비교” 설계

- **목표**: “비교할 수 있는 pair program을 먼저 만든 뒤” 비교/추상화를 시작한다는 흐름을 구현.
- **위치**: `workers/arc_solver.py`의 `test()` 루프에서, **pair1에 대해** GRID(또는 OBJECT/PIXEL) program을 **저장한 직후**에만 실행되도록 한다.
  - 예: `pair_idx >= 1`일 때, `save_program(..., level, ...)` 호출 직후에  
    `compare_pair_components(task_hex_code, pair_idx, level)` 같은 함수를 호출.
- **compare_pair_components가 할 일** (최소안):
  - Pair0와 pair_idx(예: 1)의 **같은 레벨 component**를 비교 (예: GRID면 pair0 input_grid vs pair1 input_grid, pair0 output_grid vs pair1 output_grid).
  - `compare(comp0, comp1, save=True)`로 기존 comparison 저장 규칙을 그대로 사용해도 됨 (이미 memory/… 경로에 저장됨).
  - 필요하면 “이번에 비교한 component 쌍”을 요약한 메타데이터를 `outputs/generated_codes/{task_hex_code}/{level}/` 아래에 작은 JSON으로 저장해 두면, 나중에 추상화 단계에서 “어떤 step이 어떤 component 쌍에 대응하는지”를 읽을 수 있다.
- **추상화 쪽 확장 (선택)**:
  - `anti_unify_programs` 또는 `_align_term_lists_dp`에 “pair0–pair1 component 대응” 정보를 넘기고,  
    같은 component 쌍을 다루는 step끼리 매칭 보너스를 주거나, alignment 제약으로 사용할 수 있다.
  - 이를 위해선 program의 **각 step이 어떤 component를 다룬다**는 정보가 필요하다.  
    현재 context의 `steps`에는 `line_ref`만 있으므로,  
    **나중에** `_write_context`에서 rule_id/condition과 함께 “이 step이 참조한 grid/object id” 같은 `component_ref`를 채우면, 위 매핑과 연결할 수 있다.

---

## 4. 정리

| 질문 | 답 |
|------|----|
| Flat pair program에서 추상화 가능한가? | **가능하다.** term 변환 + context(func) 기반 정렬 + anti-unify가 이미 구현되어 있음. |
| A만 써야 하나? | **아니다.** Flat만으로도 추상화 방법이 있으므로, B(대응 전제 생성)만으로도 설계 가능. 다만 A를 쓰더라도 “생성 직후 component 비교”를 넣으면 추상화 시 alignment 품질을 보조할 수 있음. |
| “비교할 수 있는 pair program을 만들고 시작”하려면? | A를 유지하고, **pair program1 저장 직후**에 pair0–pair1 **component 비교**를 한 번 호출해 두고, 그 결과를 memory/ 및 필요 시 generated_codes 쪽 메타데이터로 저장. 이후 추상화 단계에서 이 메타데이터를 선택적으로 사용. |

이 문서는 “flat에서 추상화 방법”과 “A + 생성 직후 component 비교”를 한 번에 정리한 설계 노트다. 구현 시에는 `arc_solver.test()`에 “pair_idx >= 1이고 save_program 직후”에 component 비교를 넣는 부분과, 필요 시 `_write_context`에 `component_ref`를 넣는 확장을 우선 적용하면 된다.
