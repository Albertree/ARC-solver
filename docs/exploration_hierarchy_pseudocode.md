# 계층적 탐색 (수도코드)

어떤 대상을 **어떤 공간**에서 **무엇과 비교**하는지 계층적으로 표현한 것이다.  
각 블록에서 **탐색 공간**과 **비교 대상**이 명시되어 있다.

---

## 1. TASK 수준 — 목적 세우기까지

**탐색 공간**: TASK property만으로는 목적을 세우지 못함 → PAIR 노드로 하강해 각 PAIR의 property를 확인.

```
TASK
│
├── TASK property 확인
│   │   예: { "example_pair_count": 2, "test_pair_count": 1 }
│   └── → 무엇이 없는지 알 수 없음. 목적을 세우지 못함.
│
├── 더 깊은 탐색: TASK 노드 안에 PAIR 노드가 있음
│   └── 각 PAIR 노드의 property 확인
│
├── PAIR(example).property  →  예: { "grid_count": 2 }
├── PAIR(test).property      →  예: { "grid_count": 1 }
│
└── 목적 설정: test pair에는 grid가 1개뿐 → “test pair에 없는 그리드를 생성한다”
    │   (즉, test pair의 output grid를 만드는 것이 목적 — 목적 흐름 1번 시작)
    └── 제약: “뭔가 같아야 한다” → transition이 같아야 함 (이후 PAIR 단위 탐색에서 transition 파악)
```

---

## 2. PAIR 수준 — 그리드 만들기 시도 → transition 후보 만들기

**탐색 공간**: PAIR 아래 GRID property(그리드 만들기 시도) → 실패 시 GRID 내부 요소(input_grid vs output_grid, OBJECT, PIXEL) 탐색.

Transition을 파악하기 **전에**, “그리드를 만들기 위해” PAIR 아래 있는 **GRID property**를 먼저 탐색한다.

```
PAIR(pair_idx)
│
├── [그리드 만들기 시도]  (transition 탐색 전)
│   │   탐색 공간: PAIR 아래 GRID property
│   │   목표: output grid를 “그리드 단위로” 만들 수 있는지 시도
│   │
│   │   GRID는 세 가지를 가짐: size, color, contents
│   │   하나라도 만들지 못하면 → GRID가 아님.
│   │
│   ├── 시도: size   (결정 가능한 경우 있음)
│   ├── 시도: color  (결정 가능한 경우 있음)
│   ├── 시도: contents
│   │   └── 거의 모든 상황에서 만들지 못함 → 실패
│   │
│   └── 이 실패로 인해 “GRID를 직접 만들 수 없음” → GRID 안의 요소를 탐색하는 흐름으로 전환
│
├── [GRID 내부 — 입력 vs 출력 비교]
│   │   탐색 공간: 이 PAIR 내의 "입력 그리드 vs 출력 그리드" (및 하위 요소)
│   │
│   ├── 비교: PAIR.input_grid  vs  PAIR.output_grid
│   ├── 비교 결과로 규칙 매칭 → GRID 단위 pair program 생성
│   └── (선택) GRID program 실행 → grid_result
│
├── [OBJECT 레벨]  (GRID로 해결 안 될 때)
│   │   탐색 공간: "GRID 실행 결과의 object들" vs "output_grid의 object들"
│   │
│   ├── FOR obj_i IN grid_result.objects:
│   │     FOR obj_o IN PAIR.output_grid.objects:
│   │         비교: obj_i  vs  obj_o
│   ├── 비교 결과로 규칙 매칭 → OBJECT 단위 actions → pair program에 반영
│   └── (선택) OBJECT program 실행 → object_result
│
└── [PIXEL 레벨]  (OBJECT로 해결 안 될 때)
    │   탐색 공간: "OBJECT 실행 결과의 pixel들" vs "output_grid의 pixel들"
    │
    ├── FOR pix_i IN object_result.pixels:
    │     FOR pix_o IN PAIR.output_grid.pixels:
    │         비교: pix_i  vs  pix_o
    ├── 비교 결과로 규칙 매칭 → PIXEL 단위 actions → pair program에 반영
    └── pair program 저장 (GRID/OBJECT/PIXEL 중 해당 레벨까지)
```

**요약 표**

| 단계 / 레벨 | 탐색 공간 | 비고 |
|-------------|-----------|------|
| 그리드 만들기 시도 | PAIR 아래 GRID property (size, color, contents) | contents 실패 → GRID 내부 요소 탐색으로 전환 |
| GRID 내부 | PAIR 내 두 그리드 | PAIR.input_grid vs PAIR.output_grid |
| OBJECT | GRID 실행 결과 vs 출력 그리드의 객체들 | grid_result.objects[*] vs PAIR.output_grid.objects[*] |
| PIXEL | OBJECT 실행 결과 vs 출력 그리드의 픽셀들 | object_result.pixels[*] vs PAIR.output_grid.pixels[*] |

---

## 3. PAIR 간 — PAIR component 비교 (pair0 vs pair1)

**탐색 공간**: pair0의 component들 vs pair1의 component들 (같은 역할끼리 대응).

```
PAIR_component_comparison(pair0, pair1)
│
│   탐색 공간: "pair0의 각 component" vs "pair1의 같은 종류 component"
│   목적: 어떤 것이 서로 대응하는지 매칭 정보 확보 (추상화 시 보조 정보)
│
├── [GRID 단위]
│   ├── 비교: pair0.input_grid   vs  pair1.input_grid
│   └── 비교: pair0.output_grid  vs  pair1.output_grid
│
├── [OBJECT 단위] (선택)
│   │   pair0의 output_grid.objects[*] vs pair1의 output_grid.objects[*]
│   │   (또는 대응되는 GRID끼리 묶어서 object 쌍 비교)
│   └── …
│
└── [PIXEL 단위] (선택)
    └── …
```

**요약**: 여기서의 비교는 **프로그램이 아니라** “pair0의 GRID/OBJECT 등이 pair1의 **어떤 것과 대응하는지**”를 얻기 위한 것이다. 추상화(anti-unify)의 **보조 정보**로 사용.

---

## 4. 추상화 단계 (program 간)

**탐색 공간**: “pair program”들의 **term 열** — 어느 step을 어느 step과 짝지을지, 그 쌍을 어떻게 일반화할지.

```
ABSTRACTION(task_hex_code, level)
│
│   탐색 공간: pair program0의 term 리스트 vs pair program1의 term 리스트
│   (보조: PAIR component 비교 결과 → 같은 component 대응 step끼리 매칭 보너스)
│
├── 로드: pair program0 (flat) → terms0
├── 로드: pair program1 (flat) → terms1
├── (선택) 로드: pair0–pair1 component 비교 결과
│
├── 정렬: terms0와 terms1를 쌍으로 매칭 (DP 등)
│   │   같은 func / 같은 component 대응 시 보너스
│   └── → (term0_i, term1_j) 쌍들의 열
│
├── FOR 각 (term0_i, term1_j):
│   │   anti_unify_terms(term0_i, term1_j) → (일반화 term, substitution)
│   └── → 추상 term 리스트
│
└── 추상 term 리스트 → flat 추상 프로그램 (일반화 변수 ?vN 등)
```

---

## 5. 전체 흐름 한 번에 (계층만)

```
TASK
│
├── [목적 세우기]
│   ├── TASK property 확인  →  example_pair_count, test_pair_count (목적 불명)
│   ├── 각 PAIR 노드 property 확인  →  예: grid_count (example=2, test=1)
│   └── 목적 설정: “test pair에 없는 그리드 생성” (목적 흐름 1번)
│
└── FOR each PAIR(pair_idx) in order:
    │
    ├── [그리드 만들기 시도]  (transition 전)
    │   ├── PAIR 아래 GRID property 탐색: size, color, contents
    │   └── contents 실패 (대부분)  →  GRID 내부 요소 탐색으로 전환
    │
    ├── [PAIR 내부 탐색]  (GRID 내부)
    │   ├── GRID:    compare(input_grid, output_grid)
    │   ├── OBJECT:  compare(grid_result.objects[*], output_grid.objects[*])
    │   └── PIXEL:   compare(object_result.pixels[*], output_grid.pixels[*])
    │   → pair program 저장
    │
    ├── IF pair_idx >= 1:
    │   └── [PAIR 간 탐색] PAIR_component_comparison(pair0, pair1)
    │
    └── (모든 pair 처리 후 또는 pair1 저장 직후 설계에 따라)
        └── ABSTRACTION: pair program0 + pair program1 → 추상 프로그램
```

---

이 문서는 “어떤 걸 비교하고, 어느 공간을 탐색하는지”를 수도코드·계층 구조로만 정리한 것이다.
