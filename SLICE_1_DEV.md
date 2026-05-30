# SLICE 1 — 손수 개발 가이드 (사용자 ↔ Claude 협업)

> 이건 **무인 루프가 아니다.** 사용자가 매 단계 관여하고, 풀이 trace 를 직접
> 해석하며, 모듈 하나가 끝날 때마다 멈춰서 확인한다. SOAR-ARC-test 의
> ralph loop (`docs/SLICE_1_LOOP.md`) 와 *같은 Slice 1 목표* 를 향하지만,
> 여기서는 **정밀함·이해·당위성** 이 속도보다 우선이다.
>
> **압축 경고**: 이 문서는 요약본이 아니다. §1 의 원본을 함께 보며 작업한다 —
> "그럴싸한 추상적 구현" 을 만들지 말 것.

---

## 0. 협업 원칙 (매 단계 적용)

- **모듈은 일반적, 산물은 overfit OK.** 모듈(C·D·A·B…)에 task 전용 분기를
  넣지 않는다 (일반 도구여야). 그러나 풀이로 *생겨난* program/action-sequence
  는 그 task 에 overfit 해도 정상 — 그게 나중에 anti-unification(Slice 2+)의
  입력. *통일성 검증은 모듈에만, 산물엔 적용 안 함.*
- **한 모듈 = 한 멈춤.** 모듈 하나를 만들면 멈추고, 사용자에게 *무엇을
  만들었고 / easy000a 에서 어떻게 호출되는지* 를 trace 로 보고. 사용자가
  해석하고 OK 하면 다음 모듈로.
- **정답에는 근거가 있어야 한다 (P3/P4).** 무작위·brute 값을 정답으로 제출
  금지. 모든 예측값은 *비교 결과의 COMM* 에서 논리적으로 도출.
- **검증은 4 관찰 기준** (작동 / 통일성[모듈만] / 접근성 / 탐색 건전성).
  정답 여부는 부차 신호. "이상적 14단계 재현" 을 요구하지 않는다 — 초기
  ARBOR 는 1:1 재현 못하고, 의미있는 brute-force 는 허용.

---

## 1. 함께 볼 원본 (압축본 아닌 정본)

작업 중 수시로 참조한다. 이 문서가 그 요약을 *대체하지 않는다*.

1. **`~/Desktop/wiki/raw/notion-idea-arbor-flow-three-task-description-2026-05-21.md`**
   — 사용자가 직접 쓴 풀이 시나리오 원본 (당위성·흐름의 정본). Slice 1 은
   **easy000a 문단**.
2. **`~/Desktop/wiki/wiki/arbor-execution-trace.md`** — 11 모듈 spec + 7원리.
3. **`~/Desktop/wiki/wiki/arbor-dsl-taxonomy.md`** — DSL 4종, scope selector.
4. **`~/Desktop/wiki/wiki/arbor-open-questions.md`** — 미해결 질문.
5. **`~/Desktop/ARC-solver/data/ARC_easy/`** 와 `ARBOR_flow_description/easy000a.json`
   — 실제 grid 값 (추측 금지, 직접 열어볼 것).

---

## 2. Slice 1 목표 — 그리고 당위성

`easy000a` 와 변주 `easy000a2` 를 **같은 메커니즘** 으로 푼다:

> 모든 example 의 `G1`(출력)이 동일 → role-aligned 비교 → 모든 property COMM
> → 그 공통 grid 를 test `G1` 으로 복사.

- **easy000a**: 6×6, 1×1 객체. 출력이 input 무관 *고정* `(5,5) 빨강(2)`
- **easy000a2**: 같은 메커니즘, *다른 고정 출력* (예 `(0,0) 초록(3)`)
- **G0(입력)은 Slice 1 에서 안 쓴다** (당위): 출력이 다 똑같으니 G1 비교만으로
  풀린다. 의도된 가장 쉬운 출발점 — COMM-copy 가 작동·일반적임을 먼저 증명.
- **easy000a2 의 목적**: `PredictByAllPairCommOp` 가 `(5,5)빨강` 을 하드코딩
  안 했는지 검증. 다른 고정 출력으로 *값-agnostic 일반 모듈* 만 둘 다 통과.

(G0 분석·intra 비교가 *정답에 기여* 하는 단계는 Slice 2 = easy000b.)

---

## 3. 7 원리 (모든 모듈의 설계 제약)

| P# | 원리 | Slice 1 함의 |
|----|------|-------------|
| **P1** | 계층 깊이는 *필요* 에 의해 | 막혀야 descend (TASK→PAIR→GRID), 강제 ✗ |
| **P2** | 비교는 *동일 레벨* 끼리 | GRID↔GRID 만 |
| **P3** | 정답엔 *근거* (값보다 이유) | COMM 근거 없는 값 제출 ✗ |
| **P4** | 근거는 *비교 결과* 에서 | COMM/DIFF 가 유일 정보원 |
| **P5** | 변수 출처는 **G0** | (Slice 1 은 G0 미사용이라 직접 발현은 Slice 2) |
| **P6** | *2개씩* 짝지어 | pairwise, 3-way ✗ |
| **P7** | 모든 정보 *symbolic dict+json* | 벡터 ✗ |

---

## 4. easy000a 실제 grid 와 풀이 시퀀스

### 실제 값 (json 직접 확인)

| | G0 (input) | G1 (output) |
|---|---|---|
| **P0** | (1,1) 빨강(2) | **(5,5) 빨강(2)** |
| **P1** | (1,4) 파랑(1) | **(5,5) 빨강(2)** |
| **Pa** | (4,2) 노랑(4) | **? → (5,5) 빨강(2)** |

모든 G1 완전 동일. ← Slice 1 핵심.

### 구현이 재현해야 할 시퀀스 (단계 수 정확 일치는 불필요 — §0 검증)

```
[TASK]  pair-count 확인. 형제 TASK 없음 → 비교 0 (자연 skip, P1) → intra(descend)
[PAIR]  Inter-Pair (pair property=grid-count) pairwise 3 (P6):
          compare(P0,P1)=COMM / compare(P0,Pa)=DIFF / compare(P1,Pa)=DIFF
          (score=COMM개수/전체. Pa 는 출력 가려져 grid 1개 → P0/P1 과 DIFF)
        목표(B): "Pa 에 빠진 grid(=출력) 만들기" → grid-count++ DSL 없음 → 막힘 → intra(descend)
[GRID]  Intra-Pair = descent: 막혀서 pair 안 grid 레벨로 내려감. 목표 구체화 Gx.{size,color,contents}
        내려가서 Inter 비교:
        ① 한 pair 내 G0↔G1 (정보부족, 흐름상 거침):
             compare(P0.G0, P0.G1)=DIFF, compare(P1.G0, P1.G1)=DIFF
        ② Inter-Pair-Grid (role==G1)  ★ 결정적 (P4):
             compare(P0.G1, P1.G1)=COMM(size,color,contents)
        PredictByAllPairCommOp: 모든 example G1 COMM →
             size=6×6, color={0,2}, contents=P0.G1.contents → Pa.G1 = (5,5)빨강
[OUT]   K 가 Pa.G1 제출
```

**용어 (2026-05-31 정정)**: **Intra-[component] = 비교가 아니라 descent** — 현재 레벨
정보로 목적 달성이 불가능해 *더 깊은 레벨로 내려가는 것*(예: intra-pair = pair 안으로).
**Inter-[level] = 같은 레벨 노드 property 비교** (Inter-Pair=pair끼리, Inter-Pair-Grid=
다른 pair 의 grid끼리). 내려가자마자 하위 property 를 확인·비교하므로 예전엔
"intra=비교"로 혼동됐으나, intra 는 *내려가는 행위* 자체다.

**결정적 비교**: Inter-Pair-Grid, role==G1, {size·color·contents} 전부 COMM →
test G1 = 공통값. 나머지(Inter-Pair grid-count, G0↔G1, G0역할)는 흐름상 거치되
정답엔 직접 기여 안 함.

---

## 5. 모듈 범위

**IN**: A(descent=intra) · B(goal stack) · C(Inter 비교+scope) · D(property+util) ·
K(output) · PredictByAllPairCommOp

**OUT** (Slice 2+): E·F·G·H·I·J, object/pixel property, 비교 후처리 top-k·
coordinate filter, `make_grid`/`coloring` 외 transformation (영구 금지).

---

## 6. 모듈 C 정의 + D 함수 목록 (압축 없음)

### C (scope + 비교. 모든 비교는 Inter — 같은 레벨 노드 property 비교)
```
compare(scope_A, scope_B)   # N:N (1:1=N=1), receipt. score=COMM개수/전체개수. comparison.py 재사용
compare_set(scope)          # 같은 레벨 노드들을 pairwise 비교
scope = select(anchor, level, predicate?) = filter(elements-at(anchor,level), pred)
        예: select(P0.G0, object, color-of(o)==5)
비교의 종류는 "Inter-[level]" 뿐 — 어느 scope 를 넘기냐로 갈림 (모듈은 level-agnostic):
  · Inter-Pair      : pair 끼리 (pair property, 예: grid-count)
  · Inter-Pair-Grid : 다른 pair 의 grid 끼리 (P0.G1 ↔ P1.G1, role-aligned)
※ Intra 는 비교가 아니라 descent → 모듈 A. 내려가자마자 하위 property 를 확인·비교하므로
  예전엔 "intra=비교"로 오해됐으나, intra 는 *내려가는 것* 자체다.
Slice 1: Inter-Pair(grid-count) + Inter-Pair-Grid(role==G1). 폭증 제어 미사용.
C–D 결합: scope selector 가 D 를 호출 → D 먼저 구현.
```

### D (Slice 1 필요 함수 전부 — GRID 에서 끝나므로 object/pixel property 불필요)
```
util:      pairs-of(task) / grids-of(pair) / role-of(grid: G0=input,G1=output) / filter(set,pred)
property:  (task) pair-count
           (pair) grid-count
           (grid) size / color(set) / contents
ARCKG 노드의 to_json() 키를 함수형 wrapper 로 노출 (재계산 ✗, 노출 ○).
```

---

## 7. 작업 순서 (모듈 단위 · 각 단계 후 멈춤)

현재 ARC-solver 상태: `procedural_memory/` 비어있음 (DSL 폴더 없음),
`agent/` 표준, `program/anti_unification.py` 존재 (Slice 1 미사용).

### 단계 1 — D (property + util)
- `procedural_memory/DSL/{property,util}/__init__.py` + registry. §6 함수들.
- **멈춤**: 각 함수가 easy000a 의 P0/P1/Pa 에서 올바른 값 반환하는지 사용자 확인.

### 단계 2 — C (Intra/Inter + scope selector)
- `select` = filter+util+property, `compare` = comparison.py 재사용.
- **멈춤**: easy000a 의 PAIR/GRID 비교 시퀀스(§4)가 로그로 그대로 나오는지 해석.

### 단계 3 — A (descent) + B (goal stack)
- `NeedsDescendRule` (막힘→descend, P1), `GoalStack` evolve.
- **멈춤**: TASK→PAIR→GRID 가 *막힘 때문에* 내려가는지 (강제 ✗) 확인.

### 단계 4 — PredictByAllPairCommOp + K
- example G1 들 property COMM → test G1 = 공통값 (값-agnostic). `emit_answer`.
- **멈춤**: easy000a 정답 `(5,5)빨강` 나오는지.

### 단계 5 — easy000a2 회귀 (변주)
- easy000a2 json 작성 (출력 `(0,0)초록` 등 고정, input 제각각).
- 같은 파이프라인으로 정답 → `PredictByAllPairCommOp` 일반성 확인.
- **멈춤**: 둘 다 통과 + 4 관찰 기준으로 사용자가 풀이 해석.

---

## 8. 각 멈춤에서 Claude 가 보고할 것

- 무엇을 만들었나 (파일·함수)
- easy000a 에서 *어디서 어떻게 호출* 되는가 (trace)
- 4 관찰 기준 자가 점검: 작동 / 통일성(모듈) / 접근성 / 탐색 건전성
- *막힌 지점·애매한 결정* — 사용자 판단 요청 (특히 arbor-open-questions 의
  미해결과 겹치는 부분)

사용자는 trace 를 직접 해석하고, *모듈이 일반적인지 / 산물이 적절히 overfit
인지* 가른 뒤 다음 단계 승인.

---

## 9. Slice 1 통과 후

`easy000a` + `easy000a2` 둘 다 정답 + 4 관찰 기준 만족 → Slice 1 완료.
다음은 Slice 2 (easy000b — G0 분석이 정답에 기여, intra 비교, activation rule,
anti-unification). 별도 가이드로 전환.
