# ARCKG 구현 명세서 — 코딩 에이전트 지시사항

## 목적

이 문서는 ARCKG(ARC Knowledge Graph) 시스템의 구체적인 구현 방향을 정의한다.
단순히 규칙을 추가하거나 최적화하는 방식의 개발은 금지된다.
이 명세는 아래 설계 원칙에 기반한다.

---

## 1. 시스템 전체 구조 요약

### 1-1. 노드 계층 (5단계)

```
TASK → PAIR → GRID → OBJECT → PIXEL
```

- 각 노드는 고정된 property(0차 엣지)를 가진다.
- GRID property: `size`, `color`, `contents` (3개)
- OBJECT property: `area`, `color`, `coordinate`, `method`, `position`, `shape`, `size`, `symmetry` (8개)
- PIXEL property: `color`, `coordinate` (2개)
- 모든 property 값은 symbolic (자연어도, feature vector도 아님)

### 1-2. 엣지 계층 (n차 관계)

- **0차 엣지 (property)**: 노드 자체의 속성값 dict
- **1차 엣지 (relation)**: 두 노드의 property를 compare()한 COMM/DIFF 결과 dict
- **2차 엣지**: 두 개의 1차 엣지를 compare()한 결과 dict
- **3차 엣지**: 2차 엣지와 다른 dict를 compare()한 결과 dict
- compare() 함수의 입력과 출력이 모두 dict이므로 n차 확장이 구조적으로 가능하다.

### 1-3. COMM/DIFF 비교 결과 형식

```json
{
  "type": "COMM | DIFF",
  "score": "X/N",
  "category": { ... }
}
```

- COMM: 두 값이 같음
- DIFF: 두 값이 다름
- score: 하위 category 중 COMM인 항목의 비율
- category: 재귀적으로 동일한 구조를 가짐

---

## 2. 현재 시스템의 문제점 (구현하지 말아야 할 것)

다음은 이전 개발에서 발생한 문제들로, 반복하면 안 된다.

- **규칙을 새로 만들고 최적화하는 식의 확장 금지**: 문제가 늘어날 때 규칙을 수동으로 추가하는 방식은 확장 불가능하다.
- **규칙 재사용 없음 금지**: 동일한 변환 패턴이 문제마다 새로 생성되어서는 안 된다.
- **평면적 메모리 구조 금지**: episodic, procedural memory에 구조 없이 저장하면 retrieval이 불가능하다.
- **생성된 규칙 해석 불가 금지**: 시스템이 자신이 만든 규칙을 설명할 수 없으면 안 된다.
- **지식 조합 모듈 없음 금지**: 규칙들을 합성하는 synthesizer 없이 단일 규칙만 적용하는 방식은 안 된다.

---

## 3. SOAR Operator 흐름 및 각 단계 구현 명세

### 전체 흐름

```
SelectTarget → Compare → ExtractPattern → Generalize → Predict → Submit
```

---

### 3-1. Compare

**역할**: 두 노드(주로 G0 vs G1, 또는 O_i vs O_j)의 property를 비교하여 COMM/DIFF dict를 생성한다.

**구현 조건**:
- compare() 함수는 dict → dict 변환이며 입출력 형식이 동일하다.
- Grid 레벨 비교: `size`, `color`, `contents` 3개 property 비교
- Object 레벨 비교: 8개 property 비교, score = X/8
- 비교 결과는 semantic_memory에 JSON 파일로 저장된다.

**Pruning 조건**:
- Grid의 `contents`가 COMM이면 Object 레벨 비교로 내려가지 않는다.
- 이는 탐색 공간을 줄이기 위한 탑다운 pruning이다.

---

### 3-2. Object Matching

**역할**: input grid(G0)의 각 object와 output grid(G1)의 각 object를 대응시킨다.

**구현 조건**:
- G0에 M개, G1에 N개의 object가 있으면 M×N번 비교를 수행한다.
- 각 쌍의 비교 결과 score(X/8)를 기준으로 내림차순 정렬한다.

**Threshold 규칙**:
- score > 5/8 인 쌍은 matching 후보로 취급한다 (같은 object의 변형 가능성)
- score ≤ 5/8 인 쌍은 matching 대상에서 제외한다 → creation/deletion/split/merge 케이스로 분기한다
- 이는 "야구공이 건물로 변했다"가 아니라 "다른 장면이다"라는 인지와 동일한 원리다.

**동점 처리**:
- 동일 score를 가진 쌍이 있으면 1차, 2차 relation을 추가로 확인하여 우열을 가린다.
- 그래도 결정 불가면 풀이를 branching한다.

---

### 3-3. ExtractPattern

**역할**: 여러 object 쌍의 COMM/DIFF 결과 중에서 어떤 property가 invariant인지, 어떤 property가 변해야 하는지를 결정한다.

**핵심 원칙**:
- COMM/DIFF dict 하나만 있으면 어떤 변환이든 가능하지만 근거가 약하다.
- COMM/DIFF dict가 여러 개 있으면 우열이 생긴다.
- **score가 높은 쌍(예: 7/8)에서 추출한 COMM이 score가 낮은 쌍(예: 4/8)에서 추출한 COMM보다 invariant 신뢰도가 높다.**
- 따라서 ExtractPattern은 score 내림차순으로 정렬된 matching 결과를 입력으로 받아, 상위 score 쌍에서 공통으로 나타나는 COMM property를 invariant로 결정한다.

**구현 조건**:
- score가 높은 쌍부터 순서대로 COMM property 목록을 추출한다.
- 여러 쌍에서 반복적으로 COMM인 property → invariant (고정되어야 하는 것)
- 특정 쌍에서만 DIFF인 property → transformation 대상 후보
- 결과는 WM에 슬롯으로 기록된다.

---

### 3-4. Generalize (Anti-Unification)

**역할**: 같은 task의 여러 pair에서 나온 COMM/DIFF 패턴을 2차 compare를 통해 일반화하여 추상 규칙을 생성한다.

**구현 조건**:

Step 1 — 2차 엣지 생성:
```
compare(E_P0G0-P0G1, E_P1G0-P1G1) → 2차 COMM/DIFF dict
```
P0의 input-output 비교 결과와 P1의 input-output 비교 결과를 비교한다.
2차 비교에서 COMM으로 나오는 것 = 두 pair에서 공통된 변화 패턴

Step 2 — Anti-Unification:
- 2차 비교에서 COMM인 부분 → 규칙의 고정 조건(signature)
- 2차 비교에서 DIFF인 부분 → 변수로 치환 (symbol: `"?"`)

**저장 형식** (procedural_memory에 JSON으로 저장):

```json
{
  "rule_id": "R_001",
  "order": 2,
  "signature": {
    "size": {"type": "COMM"},
    "color": {"type": "DIFF"},
    "shape": {"type": "COMM"}
  },
  "transformation": {
    "target": "color",
    "action": "DIFF",
    "variable": "?"
  },
  "source_pairs": ["T08ed6ac7.P0", "T08ed6ac7.P1"],
  "confidence": 2
}
```

- `signature`: 2차 비교에서 COMM인 부분 (이 조건을 만족하는 문제에 적용 가능)
- `transformation`: 변환 대상 property와 방향
- `variable`: "?"는 anti-unification에서 값이 달랐던 자리 (어떤 값이든 대입 가능)
- `confidence`: 이 규칙을 도출하는데 기여한 pair 수 (많을수록 신뢰도 높음)
- `source_pairs`: 출처 추적용

**저장 위치**: `procedural_memory/` — SOAR의 procedural memory와 일치한다. 별도의 저장소를 만들지 않는다.

---

### 3-5. Predict (Retrieval + Application)

**역할**: 새 문제가 들어왔을 때 저장된 규칙 중 적합한 것을 꺼내어 적용한다.

**Retrieval 조건 — 3차 compare**:

새 문제에 Compare를 수행하면 1차 COMM/DIFF dict가 생성된다.
저장된 rule의 `signature`도 COMM/DIFF dict 구조다.
따라서:

```
retrieval_score = compare(new_problem_1차_result, rule.signature)
```

이 비교에서 COMM score가 높은 rule이 retrieval 우선순위가 높다.
이는 구조적으로 3차 엣지이며, 새로운 메커니즘 없이 기존 compare() 함수를 재사용한다.

**Wildcard 처리 규칙 (compare 확장)**:

새 문제의 1차 결과는 `comp1`, `comp2` 실제 값을 포함하지만, rule의 signature는 `type`만 포함한 추상 구조다. 형태가 다르기 때문에 compare() 함수에 다음 규칙을 추가한다:

- signature 측의 값이 `"?"`이거나 해당 필드가 존재하지 않으면, 비교 결과를 **항상 COMM으로 처리**한다.
- 비교 대상은 `comp1`, `comp2`의 실제 값이 아니라 **`type` 필드(COMM/DIFF 여부)** 만이다.

즉, retrieval 시 compare()는 "새 문제에서 이 property가 COMM인가 DIFF인가"와 "rule이 요구하는 것이 COMM인가 DIFF인가"만을 대조한다. 실제 값(숫자, 좌표 등)은 retrieval 단계에서 무시된다.

**Retrieval 우선순위**:
1. retrieval_score가 가장 높은 rule을 먼저 시도한다.
2. 동점이면 confidence가 높은 rule을 우선한다.
3. 적용 후 실패하면 다음 후보로 넘어간다.

**Application**:
- 선택된 rule의 `transformation`에 따라 DSL 함수를 호출한다.
- `variable: "?"`인 자리는 현재 문제의 실제 값으로 대입된다.

---

## 4. Annotated Trace Log (풀이 과정 로그)

### 목적

터미널에 출력되는 WM 변화를 파일로 기록하고, 각 WM 변화에 대한 해석을 함께 남긴다.
이 로그는 사람이 직접 읽고 풀이 과정이 올바른지 판단하기 위한 것이다.

### 저장 위치

```
logs/trace_{task_id}_{timestamp}.log
```

`logs/` 폴더는 레포 루트에 생성한다. `.gitignore`에 추가하지 마라 — 로그가 검토 대상이다.

### 로그 형식

태스크를 시도할 때마다 아래 형식으로 로그를 누적 기록한다.
터미널 출력과 동일한 내용을 파일에도 그대로 쓴다.
각 WM 변화 블록 바로 다음에 `[해석]` 블록을 반드시 추가한다.

```
==================================================
TASK: {task_id}  |  {timestamp}
==================================================

[Cycle 1] Operator: SelectTarget
--- WM 변화 ---
(S1 ^current-task 08ed6ac7)
(S1 ^operator O1 +)
(O1 ^name select-target ^task-id 08ed6ac7)
--- [해석] ---
행동: SelectTarget operator가 제안되고 선택됨
의미: 태스크 08ed6ac7을 현재 목표로 설정함
선택 근거: 현재 WM에 ^current-task가 없었으므로 SelectTarget이 유일한 후보였음
저장 위치: WM 슬롯 (S1 ^current-task), 파일 저장 없음

[Cycle 2] Operator: Compare
--- WM 변화 ---
(S1 ^operator O2 +)
(O2 ^name compare ^target G0 ^against G1)
(S1 ^compare-result "E_P0G0-P0G1")
--- [해석] ---
행동: G0(input)와 G1(output)를 compare()로 비교함
의미: 1차 relation 엣지 생성. size=COMM(9/9), color=DIFF(5→없어짐/1234→생김), contents=DIFF
선택 근거: ^current-task가 설정된 상태에서 compare가 다음 순서 operator
저장 위치: semantic_memory/N_{task_id}/E_P0G0-P0G1.json

[Cycle 3] Operator: ExtractPattern
--- WM 변화 ---
(S1 ^invariant "size")
(S1 ^transform-target "color")
(S1 ^matching-score "7/8" ^matched-pair "G0.O0-G1.O0")
--- [해석] ---
행동: Object matching 결과에서 invariant property를 추출함
의미: G0.O0과 G1.O0의 score가 7/8로 가장 높음. size/shape/position이 COMM → invariant. color가 DIFF → transformation 대상
선택 근거: score 7/8 > threshold 5/8, 가장 높은 점수 쌍이므로 우선 처리
저장 위치: WM 슬롯 (S1 ^invariant), (S1 ^transform-target)

...

[결과]
성공 여부: SUCCESS | FAILURE
시도한 rule: R_001 (retrieval_score: 8/10)
최종 출력 그리드: semantic_memory에 저장된 predicted G1
```

### 구현 조건

- `basics/viz.py` 또는 `agent/cycle.py`에 로거를 추가한다.
- 기존 터미널 출력(`print`)을 제거하지 말고, 동시에 파일에도 쓴다 (`tee` 방식).
- `[해석]` 블록은 각 operator의 `effect()` 함수 내에서 생성한다. operator가 자신이 한 일을 설명하는 문자열을 반환하도록 구조를 수정한다.
- `[해석]` 블록에는 반드시 다음 네 항목이 포함되어야 한다:
  - `행동`: 이번 사이클에서 실행된 operator와 그 동작
  - `의미`: WM 변화가 시스템 관점에서 무엇을 뜻하는지
  - `선택 근거`: 왜 이 operator가 선택되었는지 (다른 후보 대비)
  - `저장 위치`: 이번 사이클의 결과가 WM 슬롯인지 파일인지, 어디에 저장되었는지

---

## 5. 메모리 및 로그 저장 구조 (SOAR 준수)

| 메모리 종류 | 저장 내용 | 저장 위치 |
|---|---|---|
| semantic_memory | 모든 노드 property, 1·2·3차 compare 결과 JSON | `semantic_memory/` |
| procedural_memory | anti-unification으로 생성된 추상 규칙 | `procedural_memory/` |
| episodic_memory | 태스크별 풀이 에피소드 (rule 시도 순서, 성공/실패) | `episodic_memory/` |
| logs | 태스크별 annotated trace log | `logs/` |

별도 저장소 추가 금지. SOAR의 3종 LTM 구조를 벗어나지 않는다.
`logs/`는 LTM이 아닌 관찰용 출력이므로 예외적으로 허용된다.

---

## 6. DSL 정의 (기본 실행 단위)

### 원칙

transformation은 하드코딩하지 않는다. 발견되는 것이다.
시스템이 사용할 수 있는 실행 단위는 아래 두 개뿐이다.
모든 transformation은 이 두 DSL의 조합으로 표현되어야 한다.

### DSL 목록

**1. coloring(selection, color)**

그리드의 특정 위치를 지정한 색으로 칠한다.

- `selection`: 좌표 하나 `[row, col]` 또는 좌표 리스트 `[[row, col], ...]`
- `color`: 0–9 (ARC 색상), 또는 13 (투명/null — 배경색으로 덮어씀)

```python
coloring([3, 1], 5)                          # 단일 좌표 색칠
coloring([[3,1],[4,1],[5,1]], 5)              # 다중 좌표 색칠
coloring([[3,1],[4,1]], 13)                  # 해당 위치 지움 (투명 처리)
```

**2. make_grid(height, width, color)**

새로운 그리드를 생성한다.

- `height`: 행 수
- `width`: 열 수
- `color`: 배경색 (0–9, 또는 13)

```python
make_grid(9, 9, 0)    # 9×9 검정 그리드 생성
make_grid(3, 3, 13)   # 3×3 투명 그리드 생성
```

### DSL 조합으로 표현되는 transformation 예시

이 예시는 시스템이 **발견해야 할 패턴**이지, 미리 저장된 규칙이 아니다.

| 인간이 보는 transformation | DSL 조합 |
|---|---|
| 객체 이동 (+3, +3) | `coloring(old_coords, 13)` + `coloring(shifted_coords, color)` |
| 객체 색 변경 | `coloring(coords, new_color)` |
| 객체 삭제 | `coloring(coords, 13)` |
| 그리드 크기 변경 후 복사 | `make_grid(h, w, bg)` + `coloring(coords, color)` |
| 객체 복제 | `coloring(new_coords, original_color)` |

### DIFF → DSL 변환 규칙 (Transformation Discovery)

compare()가 DIFF를 감지했을 때, `comp1`과 `comp2`의 실제 값으로부터 DSL 인자를 계산한다.
이 계산이 "transformation을 발견"하는 과정이다.

| property | DIFF 감지 시 계산 | 생성되는 DSL |
|---|---|---|
| `color` | comp2 색상값 확인 | `coloring(coords, comp2_color)` |
| `coordinate` | comp2 - comp1 = delta | `coloring(comp1_coords, 13)` + `coloring(comp1_coords + delta, color)` |
| `size` | comp2 / comp1 = ratio | `make_grid(comp2_h, comp2_w, bg)` + `coloring(...)` |
| `shape` | comp2 shape 패턴 확인 | `coloring(new_shape_coords, color)` |

이 변환 규칙은 apply_rule.py에 구현되며, DIFF 타입별로 분기하여 DSL 호출 시퀀스를 생성한다.
새로운 DIFF 패턴이 등장해도 이 구조 안에서 처리되어야 한다. 별도 함수를 추가하지 마라.

### Anti-Unification 대상

anti-unification은 COMM/DIFF 구조뿐 아니라 **생성된 DSL 시퀀스**에도 적용된다.

같은 task의 두 pair에서 동일한 DSL 시퀀스 패턴이 나오면:
```
pair0: coloring(coords_A, 13) + coloring(coords_A + [+3,+3], 5)
pair1: coloring(coords_B, 13) + coloring(coords_B + [+3,+3], 2)
```
anti-unification 결과:
```json
{
  "dsl_sequence": [
    {"fn": "coloring", "selection": "?coords", "color": 13},
    {"fn": "coloring", "selection": "?coords + [+3,+3]", "color": "?color"}
  ]
}
```
`"?"` 접두사가 붙은 값은 변수 (새 문제에서 실제 값으로 대입됨).
이 결과가 procedural_memory rule의 `transformation` 필드에 저장된다.

---

## 7. 구현 우선순위

다음 순서로 구현한다. 각 단계가 완료되고 검증된 후 다음 단계로 넘어간다.

1. **Annotated Trace Log 구현** — 모든 이후 단계의 검증 기반이므로 가장 먼저 구현한다
2. **DSL 구현** — `coloring(selection, color)`, `make_grid(h, w, color)` 두 함수만 구현한다. 다른 transformation 함수 추가 금지
3. **Object Matching 완성** — score 기반 정렬, threshold(5/8) 적용, 동점 시 branching
4. **ExtractPattern 완성** — score 높은 쌍 우선으로 invariant 결정
5. **Transformation Discovery 구현** — DIFF property 타입별로 DSL 인자 계산
6. **Generalize 완성** — 2차 compare + DSL 시퀀스 anti-unification, procedural_memory 저장
7. **Predict/Retrieval 완성** — 3차 compare로 rule retrieval, DSL 시퀀스 변수 대입
8. **Episodic memory 구조화** — 풀이 과정 에피소드 저장

---

## 8. 절대 하지 말아야 할 것

- 새 문제를 풀기 위해 규칙을 수동으로 추가하는 것
- 자연어, feature vector, 신경망 기반 표현 사용
- SOAR 3종 LTM 외 별도 저장소 생성
- compare() 함수의 입출력 형식 변경
- `coloring`과 `make_grid` 외 transformation 함수를 미리 추가하는 것
- DIFF → DSL 변환 외부에서 DSL 인자를 하드코딩하는 것
