# GRID 단계 예측 흐름 (PaG1 / test output 추론)

PAIR 간 GRID만 비교해서 test output grid를 얻고자 할 때의 논리적 흐름 정리.  
**“같다”** = grid comparison 점수 **3/3** (size, color, contents 모두 일치).

---

## 1. 목표

- **입력:** example pairs `(input_grid_k, output_grid_k)`, test pair의 `test_input_grid` (test output은 사용하지 않음).
- **출력:** `test_output_grid` 예측. 불가하면 **예측 불가**로 두고 OBJECT/PIXEL 분석으로 넘어감.
- **부가:** 다른 case에서 분석을 “완료”했는데도 grid가 하나로 정해지지 않는 경우도 이 **예측 불가**와 동일하게 보고, OBJECT/PIXEL로 넘어감.

---

## 2. 전체 단계 요약

| 단계 | 내용 | 성공 시 |
|------|------|--------|
| **1** | test input과 동일한 example input이 있는가? | `test_output_grid = output_grid_k` → **완료** |
| **2** | (1 실패) 모든 example output이 동일한가? | `test_output_grid = output_grid_k` (아무거나) → **완료** |
| **3** | (2 실패) transition 필요. **먼저 size/color** 처리 후 content | 아래 3-1 ~ 3-3 |

---

## 3. 상세 흐름

### 3-0. 전제

- Example이 0개면 **예측 불가** → OBJECT/PIXEL.
- 비교 시 “같다”는 **3/3** 기준.

### Step 1: Input 일치

```
for each example pair k:
  if grid_compare(input_grid_k, test_input_grid) == 3/3:
    test_output_grid = output_grid_k
    return SUCCESS
```

- **여러 k에서 일치하는데 output_grid_k가 서로 다른 경우:**  
  정상 task라면 발생하지 않아야 하나, 정의는 필요. → 예: **첫 번째 k 사용** 또는 **ambiguous → Step 3(transition)으로 진행**.

### Step 2: 모든 example output 동일

```
if for all k, j:  grid_compare(output_grid_k, output_grid_j) == 3/3:
  test_output_grid = output_grid_0  (아무거나)
  return SUCCESS
```

- Example이 1개면 “모두 같다”는 자동 만족.

### Step 3: Transition 필요 (size → color → content)

Step 1, 2에 해당하지 않으면 `test_output_grid = test_input_grid + transition`으로 구해야 함.  
이때 **size, color를 먼저 정한 뒤** content transition을 적용한다.

#### 3-1. Size / Color를 “위와 같은 casing”으로 추론

- **Size**
  - **(A)** 어떤 k에 대해 `size(input_grid_k) == size(test_input_grid)` → `size(test_output) = size(output_grid_k)`.
  - **(B)** 그런 k가 없으면: 모든 `size(output_grid_k)`가 같으면 → 그 공통 size를 test output size로.
- **Color**
  - **(A)** 어떤 k에 대해 test input의 color 사용이 `input_grid_k`와 같다 → 그 k의 output color 사용을 test output color로.
  - **(B)** 그런 k가 없으면: 모든 example output의 color 사용이 같으면 → 그 공통 color를 사용.

이렇게 정해진 size/color는 **3-3에서 content를 구할 때 제약으로 사용**.

#### 3-2. Size·Color transition만 계산

- 3-1에서 size/color가 하나로 정해지지 않았으면, example들로부터 **규칙** 추출 시도.
  - 예: (input size → output size), (input color → output color).
- 규칙이 있으면 test input에 적용해 test output의 **size, color만** 먼저 확정.

#### 3-3. Content (grid content transition)

- **이미 정해진 size/color가 있으면** 그 제약을 사용.
- **없으면** 제약 없이.
- Example들의 `(input_grid_k, output_grid_k)` 비교로 **content transition** 계산 후 test input에 적용 → `test_output_grid` 생성.

#### 3-4. 결과가 없거나 하나로 안 정해지는 경우

- 위 과정을 다 거쳐도 **grid가 하나로 정해지지 않거나**, 다른 case에서 “분석 완료”인데도 **grid가 생기지 않는 경우**:
  - **예측 불가**로 간주하고 **OBJECT/PIXEL 분석**으로 넘어감.

---

## 4. 예외·엣지 케이스

| 상황 | 처리 |
|------|------|
| Example 0개 | 예측 불가 → OBJECT/PIXEL |
| Step 1에서 여러 k가 input 일치하나 output 상이 | 정책 선택: 첫 번째 k 사용 **또는** ambiguous로 보고 Step 3로 |
| 1·2·3 모든 casing/transition으로도 size/color/content가 하나로 안 정해짐 | 예측 불가 → OBJECT/PIXEL |
| 다른 case 분석 “완료”했는데 grid 미생성 | 위와 동일하게 예측 불가 → OBJECT/PIXEL |

---

## 5. 코드 반영 계획 (의사코드)

아래는 `_predict_test_g1`(또는 GRID 단계 test output 예측 담당 함수)를 이 흐름에 맞게 재구성하는 의사코드이다.  
기존 `compare` 결과의 **score "x/3"** 를 사용해 “같다(3/3)”를 판단한다고 가정.

```text
FUNCTION predict_test_output_grid(examples, test_input_grid):
  IF examples is empty:
    RETURN UNPREDICTABLE  # → OBJECT/PIXEL로

  # ------ Step 1: Input 일치 ------
  FOR k IN 0..len(examples)-1:
    score = grid_compare(examples[k].input_grid, test_input_grid)
    IF score == "3/3":
      # (선택) 여러 k가 일치할 수 있음 → 첫 번째 사용 또는 output 일치 검사
      RETURN copy(examples[k].output_grid)

  # ------ Step 2: 모든 output 동일 ------
  first_output = examples[0].output_grid
  all_same = TRUE
  FOR k IN 1..len(examples)-1:
    IF grid_compare(first_output, examples[k].output_grid) != "3/3":
      all_same = FALSE
      BREAK
  IF all_same:
    RETURN copy(first_output)

  # ------ Step 3: Transition 필요 ------
  # 3-1. Size/Color casing
  pred_size = try_infer_size_by_casing(examples, test_input_grid)   # (A) input size match (B) all output size same
  pred_color = try_infer_color_by_casing(examples, test_input_grid)  # (A) input color match (B) all output color same

  # 3-2. Size/Color transition (casing으로 안 되면)
  IF pred_size is None:
    pred_size = try_compute_size_transition(examples, test_input_grid)
  IF pred_color is None:
    pred_color = try_compute_color_transition(examples, test_input_grid)

  # 3-3. Content transition (pred_size, pred_color 있으면 제약으로 사용)
  test_output = try_compute_content_transition(examples, test_input_grid, size_hint=pred_size, color_hint=pred_color)

  IF test_output is None OR not uniquely_determined(test_output):
    RETURN UNPREDICTABLE  # → OBJECT/PIXEL로

  RETURN test_output
```

### 보조 함수 (의사코드)

```text
# "같다" = 3/3. 기존 compare 결과의 result["score"] 사용.
FUNCTION grid_compare(grid_a, grid_b) -> "x/3"

# Size casing: (A) size(in_k)==size(test_in)인 k 있으면 out_k의 size (B) 모든 out size 같으면 그 값
FUNCTION try_infer_size_by_casing(examples, test_input_grid) -> size or None

# Color casing: (A) color 사용이 in_k와 같은 k 있으면 out_k의 color (B) 모든 out color 같으면 그 값
FUNCTION try_infer_color_by_casing(examples, test_input_grid) -> color_spec or None

# Example들의 input size → output size 규칙 추출 후 test input에 적용
FUNCTION try_compute_size_transition(examples, test_input_grid) -> size or None

# Example들의 input color → output color 규칙 추출 후 test input에 적용
FUNCTION try_compute_color_transition(examples, test_input_grid) -> color_spec or None

# Example들의 (input, output) 비교로 content transition 규칙 추출, test input에 적용.
# size_hint/color_hint가 있으면 생성 그리드가 그 제약을 만족하도록.
FUNCTION try_compute_content_transition(examples, test_input_grid, size_hint, color_hint) -> grid or None
```

### 호출부 연동

```text
# 기존 test() 흐름에서
pred = predict_test_output_grid(task.example_pairs, test_pair.input_grid)

IF pred != UNPREDICTABLE:
  self._test_output_prediction = pred
  IF pred == task.test_pair.output_grid (3/3):  # 채점용
    self._pa_g1_prediction_correct = True
    RETURN  # pair program 생성 생략
ELSE:
  # 예측 불가 또는 다른 case에서 grid 미생성
  self._finished_by_pa_g1_prediction = False
  # → 기존대로 PAIR별 GRID/OBJECT/PIXEL 프로그램 생성·실행으로 진행
```

---

## 6. 현재 코드와의 대응

- **현재:** `_predict_test_g1`에서 “example G1들의 size/color/contents가 **모두 동일**”할 때만 예측 후보를 넣고, 그걸 그대로 test output으로 씀 (실질적으로 Step 2만 구현된 형태).
- **목표:**  
  - Step 1 (input 일치) 추가.  
  - Step 2는 유지하되 “3/3” 명시.  
  - Step 3: size/color casing → size/color transition → content transition 순서로 확장.  
  - 어디서든 grid가 하나로 정해지지 않거나, 다른 분석에서 grid가 안 나오면 **UNPREDICTABLE**로 두고 OBJECT/PIXEL로 넘기기.

이 문서와 5절 의사코드를 기준으로 `_predict_test_g1` 및 관련 비교/규칙 추출 로직을 단계적으로 리팩터링하면 된다.
