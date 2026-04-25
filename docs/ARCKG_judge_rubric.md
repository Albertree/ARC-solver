# ARCKG LLM-as-Judge 루브릭

## Judge 역할 정의

Judge는 Developer LLM이 생성한 코드와 실행 결과를 평가한다.
Judge는 ARCKG_implementation_spec.md를 유일한 정답 기준으로 삼는다.
Judge의 출력은 항상 다음 형식을 따른다:

```json
{
  "phase": "현재 평가 대상 단계",
  "score": "X/100",
  "passed_criteria": [...],
  "failed_criteria": [...],
  "critical_violations": [...],
  "next_instruction": "Developer에게 전달할 구체적 지시"
}
```

`critical_violations`가 하나라도 있으면 `score`와 무관하게 루프를 계속한다.
`score >= 80` 이고 `critical_violations == []` 일 때만 다음 Phase로 진행한다.

---

## 절대 위반 항목 (Critical Violations)

다음 중 하나라도 발생하면 즉시 해당 코드를 전면 거부하고 재작성을 지시한다.
점수 계산 이전에 먼저 확인한다.

| 코드 | 위반 내용 |
|---|---|
| CV-01 | 새 문제를 풀기 위해 규칙을 수동으로 추가함 |
| CV-02 | 자연어 문자열, feature vector, 신경망을 지식 표현에 사용함 |
| CV-03 | semantic_memory / procedural_memory / episodic_memory 외 별도 저장소를 생성함 |
| CV-04 | compare() 함수의 입출력 형식(dict→dict, type/score/category 구조)을 변경함 |
| CV-05 | transformation 함수 목록을 코드에 하드코딩하여 미리 고정함 |
| CV-06 | 동일한 변환 패턴이 문제마다 새로 생성되고 재사용되지 않음 |

---

## Phase 0: Annotated Trace Log

### 평가 대상

`logs/` 폴더 생성 여부 및 로그 파일 내용

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P0-01 | `python run_task.py` 실행 시 `logs/trace_{task_id}_{timestamp}.log` 파일이 생성된다 | 20 |
| P0-02 | 터미널 출력이 로그 파일에도 동일하게 기록된다 (tee 방식, 기존 print 제거 금지) | 15 |
| P0-03 | 각 Cycle 블록에 `[해석]` 섹션이 존재한다 | 20 |
| P0-04 | `[해석]`에 `행동`, `의미`, `선택 근거`, `저장 위치` 네 항목이 모두 있다 | 25 |
| P0-05 | `저장 위치` 항목이 실제 파일 경로 또는 WM 슬롯명을 명시한다 (추상적 기술 금지) | 10 |
| P0-06 | 로그 마지막에 `[결과]` 블록이 있고 성공/실패, 시도한 rule_id가 기록된다 | 10 |

### Judge 판정 기준

- P0-01이 실패하면 (파일이 생성되지 않으면) Phase 0 전체 재작성. 이후 Phase로 진행 불가.
- P0-04에서 네 항목 중 하나라도 빠지면 실패로 처리한다.
- `[해석]`이 모든 Cycle에 없고 일부에만 있으면 P0-03 실패.
- 로그를 읽고 사람이 풀이 흐름을 이해할 수 있는지를 최종 판단 기준으로 삼는다.

---

## Phase 1: Object Matching

### 평가 대상

`agent/active_operators.py` 또는 Compare operator의 object matching 로직

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P1-01 | G0의 M개 object와 G1의 N개 object에 대해 M×N번 비교를 수행한다 | 15 |
| P1-02 | 각 쌍의 비교 결과 score(X/8)를 기준으로 내림차순 정렬한다 | 15 |
| P1-03 | score > 5/8 인 쌍만 matching 후보로 처리한다 | 20 |
| P1-04 | score ≤ 5/8 인 쌍은 creation/deletion/split/merge 케이스로 분기한다 | 20 |
| P1-05 | 동점 쌍이 있을 때 1차·2차 relation을 추가 확인하여 우열을 가린다 | 15 |
| P1-06 | 그래도 결정 불가면 풀이를 branching한다 (단일 경로 강제 금지) | 15 |

### Judge 판정 기준

- P1-03, P1-04가 모두 실패하면 CV-01에 준하는 위반으로 간주한다.
- threshold 값(5/8)이 하드코딩이 아닌 설정값으로 분리되어 있으면 +5 보너스.

---

## Phase 1.5: DSL 구현 및 Transformation Discovery

### 평가 대상

`dsl/coloring.py`, `dsl/make_grid.py` (또는 동등한 위치), `agent/apply_rule.py`의 DIFF→DSL 변환 로직

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P15-01 | `coloring(selection, color)` 함수가 구현되어 있다 | 10 |
| P15-02 | `selection`이 단일 좌표와 좌표 리스트 모두 처리한다 | 10 |
| P15-03 | `color` 13이 투명(배경색 덮어쓰기)으로 처리된다 | 10 |
| P15-04 | `make_grid(height, width, color)` 함수가 구현되어 있다 | 10 |
| P15-05 | 이 두 함수 외 다른 transformation 함수가 추가되어 있지 않다 | 15 |
| P15-06 | `color` DIFF 시 `coloring(coords, comp2_color)` DSL이 생성된다 | 10 |
| P15-07 | `coordinate` DIFF 시 delta 계산 후 `coloring(old, 13)` + `coloring(new, color)` 시퀀스가 생성된다 | 15 |
| P15-08 | `size` DIFF 시 `make_grid(comp2_h, comp2_w, bg)` + `coloring(...)` 시퀀스가 생성된다 | 10 |
| P15-09 | DSL 인자가 DIFF의 `comp1`, `comp2` 값에서 계산되며 하드코딩되지 않는다 | 10 |

### Judge 판정 기준

- P15-05가 실패하면 (다른 transformation 함수가 추가되었으면) CV-05 위반으로 즉시 거부.
- P15-09가 실패하면 (DSL 인자가 하드코딩이면) CV-01에 준하는 위반으로 재작성 지시.
- P15-06~P15-08 중 하나라도 실패하면 Transformation Discovery가 미완성이므로 Phase 진행 불가.

---

## Phase 2: ExtractPattern

### 평가 대상

ExtractPattern operator의 invariant 결정 로직

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P2-01 | 입력으로 Phase 1의 정렬된 matching 결과(score 내림차순)를 받는다 | 10 |
| P2-02 | score가 높은 쌍부터 순서대로 COMM property 목록을 추출한다 | 20 |
| P2-03 | 여러 쌍에서 반복적으로 COMM인 property를 invariant로 결정한다 | 25 |
| P2-04 | 특정 쌍에서만 DIFF인 property를 transformation 대상 후보로 기록한다 | 25 |
| P2-05 | 결과를 WM 슬롯으로 기록한다 (별도 파일 저장 아님) | 20 |

### Judge 판정 기준

- P2-02와 P2-03이 모두 실패하면 "score 무관하게 COMM을 선택"하는 이전 방식과 동일하므로 재작성 지시.
- score 가중치 로직이 명시적으로 코드에 존재하는지 확인한다. 암묵적 처리는 감점.

---

## Phase 3: Generalize (Anti-Unification)

### 평가 대상

`program/anti_unification.py` 및 Generalize operator

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P3-01 | 같은 task의 두 pair 비교 결과(1차 엣지)를 compare()에 입력하여 2차 엣지를 생성한다 | 20 |
| P3-02 | 2차 비교에서 COMM인 부분을 rule의 `signature`로 추출한다 | 20 |
| P3-03 | 2차 비교에서 DIFF인 부분을 `"?"`로 치환한다 | 15 |
| P3-04 | 결과를 아래 정확한 JSON 형식으로 procedural_memory에 저장한다 | 25 |
| P3-05 | `confidence` 필드가 기여한 pair 수로 설정된다 | 10 |
| P3-06 | `source_pairs` 필드가 출처 pair ID 목록으로 설정된다 | 10 |

**P3-04 요구 형식 (정확히 일치해야 함)**:
```json
{
  "rule_id": "R_XXX",
  "order": 2,
  "signature": {
    "[property명]": {"type": "COMM | DIFF"}
  },
  "transformation": {
    "target": "[property명]",
    "action": "DIFF",
    "variable": "?"
  },
  "source_pairs": ["[pair_id_1]", "[pair_id_2]"],
  "confidence": N
}
```

### Judge 판정 기준

- P3-04 형식이 다르면 CV-04에 준하는 위반으로 간주하고 재작성 지시.
- 2차 엣지 생성 없이 바로 규칙을 만들면 P3-01 실패로 전체 Phase 재작성.

---

## Phase 4: Predict (Retrieval + Application)

### 평가 대상

Predict operator의 retrieval 로직 및 compare() 확장

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P4-01 | 새 문제의 1차 COMM/DIFF 결과와 저장된 rule의 signature를 compare()로 비교한다 | 20 |
| P4-02 | 이 비교가 3차 엣지로 semantic_memory에 기록된다 | 10 |
| P4-03 | retrieval 시 compare()는 `type` 필드(COMM/DIFF)만 대조한다 (`comp1`, `comp2` 실제 값 무시) | 25 |
| P4-04 | signature 측 값이 `"?"`이거나 필드가 없으면 해당 항목을 COMM으로 처리한다 | 20 |
| P4-05 | retrieval_score가 높은 rule을 먼저 시도한다 | 10 |
| P4-06 | 동점이면 confidence가 높은 rule을 우선한다 | 5 |
| P4-07 | 적용 후 실패하면 다음 후보 rule로 넘어간다 (단일 시도 후 포기 금지) | 10 |

### Judge 판정 기준

- P4-03, P4-04가 모두 실패하면 retrieval이 동작하지 않으므로 Phase 4 전체 재작성.
- compare()에 wildcard 처리를 위한 모드 플래그(또는 별도 함수)가 명시적으로 존재하는지 확인.

---

## Phase 5: Episodic Memory 구조화

### 평가 대상

`episodic_memory/` 저장 로직 및 에피소드 형식

### 체크리스트

| ID | 기준 | 배점 |
|---|---|---|
| P5-01 | 각 태스크 풀이마다 에피소드가 생성된다 | 15 |
| P5-02 | 에피소드에 시도한 rule_id 목록이 순서대로 기록된다 | 25 |
| P5-03 | 각 rule 시도의 성공/실패 여부가 기록된다 | 25 |
| P5-04 | 실패한 경우 실패 이유가 기록된다 (어떤 property에서 불일치했는지) | 20 |
| P5-05 | 에피소드가 dict 형식으로 JSON 저장된다 (다른 메모리와 형식 일관성 유지) | 15 |

---

## 통합 실행 결과 평가

각 Phase를 통과한 후, 실제 ARC 태스크를 실행하여 다음을 확인한다.

| ID | 기준 | 판정 방식 |
|---|---|---|
| E-01 | 한 번 푼 문제와 유사한 문제를 풀 때 저장된 rule이 retrieval된다 | episodic_memory 로그 확인 |
| E-02 | retrieval된 rule이 실제로 적용된다 | 실행 trace 확인 |
| E-03 | 문제를 풀 때 새 규칙이 수동으로 추가되지 않는다 | git diff 확인 (코드 변경 없어야 함) |
| E-04 | 같은 태스크를 두 번 실행하면 두 번째가 더 빠르다 (retrieval 효과) | 실행 시간 비교 |
| E-05 | 처음 보는 문제에서 가장 유사한 rule이 먼저 시도된다 | retrieval_score 로그 확인 |

E-03이 실패하면 (코드가 변경되었으면) CV-01 위반으로 즉시 거부한다.

---

## Judge 루프 운영 지침

### Developer에게 전달하는 next_instruction 작성 원칙

1. **실패한 기준의 ID를 명시한다** — "P2-02가 실패했습니다" 처럼 추상적으로 쓰지 않는다.
2. **수정해야 할 파일과 함수명을 명시한다** — "agent/active_operators.py의 ExtractPattern.effect() 내 invariant 선택 로직을 수정하라"
3. **기대하는 동작을 코드 수준으로 기술한다** — "score 내림차순 정렬된 리스트를 순회하며 2회 이상 등장한 COMM property만 invariant로 등록해야 한다"
4. **이전 시도에서 발생한 CV 항목을 반드시 포함한다** — 같은 위반이 반복되면 접근 방식 자체를 재설계하도록 지시한다.

### 루프 종료 조건

- Phase 1~5 모두 score >= 80, critical_violations == []
- 통합 실행 평가 E-01~E-05 모두 통과
- 위 두 조건을 동시에 만족할 때 루프를 종료한다.
