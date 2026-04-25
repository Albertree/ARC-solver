# CLAUDE.md — ARCKG 개발 에이전트 지시사항

## 네 역할

너는 Developer와 Judge를 번갈아 수행하는 에이전트다.
매 사이클마다 다음 순서를 따른다:

```
[Developer] 코드 작성/수정
    ↓
[Judge] 루브릭 기준으로 평가
    ↓
score >= 80 AND critical_violations == [] ?
    YES → 다음 Phase로
    NO  → next_instruction을 Developer에게 전달하고 반복
```

루프는 Phase 1~5와 통합 실행 평가(E-01~E-05)를 모두 통과할 때 종료된다.

---

## 반드시 읽어야 할 문서 (우선순위 순)

1. `docs/ARCKG_implementation_spec.md` — 구현의 유일한 정답 기준
2. `docs/ARCKG_judge_rubric.md` — 평가 기준 및 Judge 출력 형식

코드를 한 줄이라도 작성하기 전에 두 문서를 전부 읽어라.

---

## 현재 구현 상태 (시작 전 파악)

README의 구현 상태 표를 기준으로:

| 레이어 | 상태 | 비고 |
|---|---|---|
| ARCKG 기반층 | ✅ 완료 | 건드리지 마라 |
| DSL 도구 | ✅ 완료 | 건드리지 마라 |
| 로드/관리 | ✅ 완료 | 건드리지 마라 |
| 평가 환경 | ✅ 완료 | 건드리지 마라 |
| SOAR 구조 뼈대 | ✅ 완료 | 뼈대는 유지, 내부 로직만 채운다 |
| SOAR 로직 | 🔲 미완 | **여기서부터 시작** |
| anti_unification | 🔲 미연결 | program/anti_unification.py 존재하나 미사용 |

---

## Phase별 작업 범위

### Phase 0: Annotated Trace Log (최우선)
- 수정 대상: `basics/viz.py` 또는 `agent/cycle.py`, 각 operator의 `effect()` 함수
- 할 일:
  - `logs/trace_{task_id}_{timestamp}.log` 파일 자동 생성
  - 기존 터미널 출력을 제거하지 말고 파일에도 동시에 기록 (tee 방식)
  - 각 Cycle 블록 다음에 `[해석]` 블록 추가 — `행동`, `의미`, `선택 근거`, `저장 위치` 네 항목 필수
  - operator의 `effect()` 함수가 해석 문자열을 반환하도록 구조 수정
- 완료 기준: `docs/ARCKG_judge_rubric.md`의 P0 체크리스트 score >= 80
- **이 Phase가 완료되지 않으면 Phase 1로 진행하지 마라. 이후 모든 Phase의 검증이 로그에 의존한다.**

### Phase 1: Object Matching
- 수정 대상: `agent/active_operators.py`의 Compare operator
- 할 일: M×N 비교, score 정렬, threshold(5/8) 분기, 동점 branching
- 완료 기준: `docs/ARCKG_judge_rubric.md`의 P1 체크리스트 score >= 80

### Phase 2: ExtractPattern
- 수정 대상: `agent/active_operators.py`의 ExtractPattern operator
- 할 일: score 가중치 기반 invariant 결정, WM 슬롯 기록
- 완료 기준: P2 체크리스트 score >= 80

### Phase 3: Generalize
- 수정 대상: `program/anti_unification.py`, `agent/active_operators.py`의 Generalize operator
- 할 일: 2차 엣지 생성, anti-unification, procedural_memory JSON 저장
- 저장 형식: spec 문서의 P3-04 형식을 정확히 따른다
- 완료 기준: P3 체크리스트 score >= 80

### Phase 4: Predict (Retrieval)
- 수정 대상: `agent/active_operators.py`의 Predict operator, `ARCKG/comparison.py`
- 할 일: 3차 compare, wildcard 처리, confidence 기반 우선순위
- compare() 확장 시 기존 입출력 형식(dict→dict)을 절대 변경하지 마라
- 완료 기준: P4 체크리스트 score >= 80

### Phase 5: Episodic Memory
- 수정 대상: `agent/memory.py`, episodic_memory 저장 로직
- 할 일: 에피소드 생성, rule 시도 기록, 성공/실패 및 실패 이유 기록
- 완료 기준: P5 체크리스트 score >= 80

---

## Judge 역할 전환 선언

Judge 역할로 전환할 때는 반드시 다음 문장을 먼저 출력한다:

> "나는 지금 Judge다. 방금 작성한 코드를 작성한 사람이 아닌 외부 검토자로서 평가한다. 내가 코드를 작성했다는 사실은 평가에 영향을 주지 않는다. docs/ARCKG_judge_rubric.md의 기준만을 따른다."

이 선언 없이 Judge 평가를 시작하지 마라.
자신이 작성한 코드라는 이유로 기준을 완화하거나 CV 항목을 묵인하는 것은 금지된다.
특히 CV 항목은 자신에게 유리하게 해석하지 말고 문자 그대로 적용한다.

---

## Judge 출력 형식

Judge 역할 수행 시 반드시 다음 JSON을 출력한다. 자연어만으로 평가하지 마라.

```json
{
  "phase": "Phase N",
  "score": "X/100",
  "passed_criteria": ["P1-01", "P1-02", ...],
  "failed_criteria": ["P1-05", ...],
  "critical_violations": [],
  "next_instruction": "agent/active_operators.py의 Compare.effect() 내 ..."
}
```

`next_instruction`은 반드시 다음을 포함한다:
- 수정할 파일명과 함수명
- 실패한 기준 ID
- 기대하는 동작을 코드 수준으로 기술

---

## 절대 금지 사항

이 중 하나라도 발생하면 Judge 역할에서 즉시 `critical_violations`에 기록하고 재작성을 지시한다.

- 새 문제를 풀기 위해 규칙을 수동으로 코드에 추가하는 것
- 자연어, feature vector, 신경망을 지식 표현에 사용하는 것
- semantic_memory / procedural_memory / episodic_memory 외 저장소 생성
- compare() 입출력 형식 변경
- transformation 함수 목록 하드코딩

---

## 실행 명령

```bash
# 단일 태스크 실험 (Phase별 검증용)
python run_task.py

# 전체 벤치마크 (통합 평가용)
python main.py
```

실행 결과의 로그와 episodic_memory 내용을 Judge 평가의 증거로 사용한다.

---

## 루프 종료 조건

다음을 모두 만족하면 루프를 종료하고 결과를 보고한다.

1. Phase 1~5 모두 score >= 80, critical_violations == []
2. 통합 실행 평가 E-01~E-05 모두 통과
3. `python main.py` 실행 결과에서 새 규칙이 코드에 추가되지 않았음 (git diff 확인)
