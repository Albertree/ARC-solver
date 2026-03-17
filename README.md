# ARCKG — ARC Knowledge Graph Solver

순수 심볼릭 AI 시스템으로 ARC(Abstraction and Reasoning Corpus) 태스크를 푼다.  
계층적 지식 그래프를 구축하고 SOAR 인지 아키텍처를 sole solver로 운용한다.

---

## 핵심 철학

- **순수 심볼릭** — 지식 레이어에 신경망 없음
- **지식은 관계(why)로 저장**, 프로그램(how)이 아님
- **실패(impasse)는 정보** — 무엇이 부족한지 드러냄
- **SOAR가 유일한 solver** — 별도의 프로그램 합성 엔진 없음

---

## 실행

```bash
# 전체 벤치마크
python main.py

# 단일 태스크 실험 (에러 추적용)
python run_task.py
```

---

## 모듈 구조

```
ARC-solver2/
│
├── main.py                  ← 단일 진입점
├── run_task.py              ← 단일 태스크 실험 스크립트
│
├── ARCKG/                   ← Knowledge Graph 기반층
│   ├── task.py              TASK 노드   (T{hex})
│   ├── pair.py              PAIR 노드   (T.P{n})
│   ├── grid.py              GRID 노드   (T.P.G{n})
│   ├── object.py            OBJECT 노드 (T.P.G.O{n})
│   ├── pixel.py             PIXEL 노드  (T.P.G.O.X{n})
│   ├── hodel.py             객체 검출 함수 (Hodel's objects())
│   ├── comparison.py        compare() — 핵심 관계 구축 함수
│   └── memory_paths.py      노드 ID → 파일 경로 변환
│
├── agent/                   ← SOAR 인지 아키텍처 (유일한 solver)
│   ├── wm.py                WorkingMemory — WME triplet, S1/S2 상태 스택
│   ├── elaboration_rules.py ElaborationRule, Elaborator — 파생 사실 생성
│   ├── rules.py             ProductionRule, Proposer — operator 후보 제안
│   ├── operators.py         Operator 베이스 클래스
│   ├── active_operators.py  SelectTarget / Compare / ExtractPattern /
│   │                        Generalize / Predict / Submit
│   ├── preferences.py       select_operator() — PREFERENCE_ORDER 기반 선택
│   ├── cycle.py             run_cycle() — Elaborate→Propose→Select→Apply 루프
│   ├── agent_common.py      build_wm_from_task / goal_satisfied / answers_from_wm
│   ├── memory.py            chunk_from_substate / LTM 저장·로드
│   └── active_agent.py      ActiveSoarAgent — env 호환 agent 인터페이스
│
├── env/                     ← 평가 환경
│   └── arc_environment.py   ARCEnvironment — 태스크 제공, 채점, trace
│
├── managers/
│   └── arc_manager.py       ARCManager — data/ 로드 → ARCKG 노드 계층 구성
│
├── program/
│   └── anti_unification.py  관계 trace → 추상 규칙 일반화
│
├── procedural_memory/DSL/   ← DSL 도구 (operator 내부 호출용)
│   ├── apply.py             apply_DSL() 디스패처
│   ├── transformation.py    그리드/객체 변환 함수
│   ├── selection.py         find_object()
│   ├── util.py              헬퍼
│   └── layer.py             90×90 캔버스 레이어 시스템
│
├── basics/
│   ├── viz.py               ANSI 컬러 시각화 (show_task / show_objects / show_comparison)
│   └── utils.py             기타 유틸리티
│
├── data/                    ← symlink → ../ARC-solver/data (read-only)
├── semantic_memory/         ← STORAGE: KG 노드 속성 + 비교 엣지 (JSON)
├── episodic_memory/         ← STORAGE: 태스크별 풀이 에피소드
└── inspect.py               ← 디버깅용 대화형 스크립트
```

---

## 지식 그래프 구조

### 5계층 노드 계층

```
TASK (T{hex})
 └── PAIR (P{n} / Pa,Pb,...  for test)
      └── GRID (G0=input, G1=output)
           └── OBJECT (O{n})
                └── PIXEL (X{n})
```

### 노드 = 폴더, 엣지 = JSON 파일

```
semantic_memory/
  N_T{hex}/
    E_T{hex}.json          ← 0th-order: TASK 속성
    E_P0G0-P0G1.json       ← 1st-order: G0 vs G1 비교
    E_(E_...)-(...).json   ← 2nd-order: 관계 간 비교
    N_T{hex}.P0/
      E_P0.json            ← PAIR 속성
      E_P0G0.json          ← GRID 속성
      ...
```

### 관계 결과 형식

```json
{
  "id1": "T08ed6ac7.P0.G0",
  "id2": "T08ed6ac7.P0.G1",
  "lca_node_id": "T08ed6ac7.P0",
  "order": 1,
  "result": {
    "type": "COMM | DIFF",
    "score": "2/3",
    "category": { ... }
  }
}
```

---

## SOAR 결정 사이클

```
매 사이클:
  ① Elaborate  — ElaborationRule들을 fixed-point까지 반복
                  → wm.elaborated 채움
  ② Propose    — ProductionRule들이 elaborated 읽어 operator 후보 수집
  ③ Select     — PREFERENCE_ORDER 기준으로 하나 선택
  ④ Apply      — operator.effect(wm) 호출 → WM에 새 사실 추가
  
  impasse 발생 조건:
    - 후보 없음 (no_candidates) → substate 생성
    - op_status = failure       → substate 생성
  
  MAX_SUBSTATE_DEPTH = 2
```

### Operator 흐름

```
SelectTarget → Compare → ExtractPattern → Generalize → Predict → Submit
(agenda에서   (관계 생성) (COMM→invariant  (추상 규칙   (test 출력  (goal
pending으로)             DIFF→diff_pattern) 생성·저장)  예측)       완료)
```

---

## 환경 인터페이스

```python
env = ARCEnvironment(task_list=["08ed6ac7"], time_budget_sec=300)
agent = ActiveSoarAgent(semantic_memory_root="semantic_memory")
results = env.run_benchmark(agent)
# → {"correct": int, "total": int, "results": list, "trace": list}
```

- `agent.solve(task)` → `list[list[list[int]]]` (test pair 수만큼의 출력 그리드)
- `agent.can_retry` → `bool` (최대 3회 제출)
- reward: 1.0 = 전부 정답, 0.0 = 하나라도 오답 (부분 점수 없음)

---

## 데이터

```bash
ln -s ../ARC-solver/data ./data   # 최초 1회 심볼릭 링크 생성
```

`data/`는 read-only. 절대 수정하지 마.

---

## 구현 상태

| 레이어 | 파일 | 상태 |
|--------|------|------|
| ARCKG 기반층 | ARCKG/*.py | ✅ 완료 |
| DSL 도구 | procedural_memory/DSL/*.py | ✅ 완료 |
| 로드/관리 | managers/arc_manager.py | ✅ 완료 |
| 평가 환경 | env/arc_environment.py | ✅ 완료 |
| SOAR 구조 | agent/*.py | ✅ 뼈대 완료 |
| SOAR 로직 | agent/wm.py 외 | 🔲 구현 필요 |
| 진입점 | main.py | ✅ 완료 |
