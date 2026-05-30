# SLICE 2 — 손수 개발 가이드 (easy000c + easy000d 회귀)

> Slice 1(easy000a/b)을 이어, **G0(입력)가 정답에 기여**하는 첫 슬라이스. 출력이
> 더는 고정이 아니라 *입력에 의존*(색)하므로, **intra-pair 비교가 결정적**이 되고
> **변수(색)의 출처가 G0**(P5)이 처음으로 발현한다. Slice 1 코드(`agent/descent.py`,
> `agent/predict.py`, `procedural_memory/DSL`)를 *확장*한다 — 재작성 ✗.
>
> **압축 경고**: 요약본 아님. §1 원본 + Slice 1 코드를 함께 보며 작업. "그럴싸한 추상" ✗.

---

## 0. 협업 원칙 (Slice 1 §0 그대로)

- **모듈은 일반적, 산물은 overfit OK.** 통일성 검증은 모듈에만.
- **한 모듈 = 한 멈춤.** 만들면 멈추고 trace로 보고 → 사용자 해석 → 승인 → 다음.
- **정답엔 근거 (P3/P4).** brute 값 ✗, 비교(COMM/DIFF·intra/inter) 결과에서 도출.
- **검증은 4 관찰 기준** (작동 / 통일성[모듈] / 접근성 / 탐색 건전성). 정답은 부차 신호.

---

## 1. 함께 볼 원본

1. `~/Desktop/wiki/wiki/arbor-execution-trace.md` — 11 모듈 + Slice 계획 (Slice 2 절).
2. `~/Desktop/wiki/wiki/arbor-memory-contents.md` — **semantic = DSL 추상 라이브러리**.
   Slice 2 의 anti-unify 산물이 여기로 deposit 되기 시작.
3. `~/Desktop/wiki/wiki/anti-unification.md` — 일반화 연산 정본.
4. `SLICE_1_DEV.md` — 용어(Intra=descent / Inter=비교), 7원리, 모듈 C/D 정의.
5. `data/ARC_easy_a/{easy000c,easy000d}.json` + `README.md` — 실제 grid (직접 열 것).
6. **Slice 1 코드** — `agent/descent.py`(A), `goal_stack.py`(B), `predict.py`,
   `procedural_memory/DSL/{util,property,relation,transformation}`. Slice 2 는 이걸 확장.

---

## 2. Slice 2 목표 — 그리고 당위성

`easy000c` 와 변주 `easy000d` 를 **같은 메커니즘** 으로 푼다:

> 출력 = 한 객체. **위치는 고정(COMM across pairs)**, **색은 입력 객체색을 복사(G0)**.
> intra-pair(G0↔G1)에서 *색 보존* 이 드러나는 게 결정적.

- **easy000c**: 출력 `(5,5)` = 입력색 (위치 5,5 고정)
- **easy000d**: 같은 메커니즘, *다른 고정 위치* `(1,2)` = 입력색
- **G0 를 Slice 2 에서 *쓴다* (당위)**: 출력이 입력색에 의존하므로 G0 분석 없이는 색을
  못 정함. Slice 1 에서 "흐름상 거치던" intra-pair(G0↔G1)가 여기선 *정답의 근거*.
- **P5 발현**: 답에 **변수(색)** 가 생기고 그 **출처가 G0**. Slice 1 엔 변수가 없었다(고정).
- **easy000d 의 목적**: predictor 가 `(5,5)` 위치나 특정 색을 하드코딩 안 했는지 검증
  (위치-agnostic + 색-agnostic). 같은 코드로 c·d 둘 다 통과.

(크기·위치가 *관계* 에서 나오는 e·f·g 는 Slice 3 — 다중 변수·관계 도입.)

---

## 3. 7 원리 — Slice 2 함의

| P# | 원리 | Slice 2 함의 |
|----|------|-------------|
| **P1** | 깊이는 *필요* 에 | GRID 가 *부분 COMM*(size만)이라 막힘 → **OBJECT 로 더 하강** |
| **P2** | 동일 레벨 비교 | OBJECT↔OBJECT |
| **P3** | 정답엔 근거 | 위치=inter-COMM, 색=intra-preserved 근거 |
| **P4** | 근거는 비교 결과 | inter(위치) + intra(색) 두 비교가 함께 답을 정함 |
| **P5** | 변수 출처는 **G0** | **여기서 발현** — 색 변수 = G0 객체색 |
| **P6** | 2개씩 | pairwise |
| **P7** | symbolic dict+json | object property·receipt·anti-unify schema 전부 json |

---

## 4. easy000c 실제 grid 와 풀이 시퀀스

### 실제 값 (json 직접 확인)
| | G0 (input) | G1 (output) |
|---|---|---|
| **P0** | (1,1) 빨강(2) | (5,5) 빨강(2) |
| **P1** | (1,4) 파랑(1) | (5,5) 파랑(1) |
| **Pa** | (4,2) 노랑(4) | **? → (5,5) 노랑(4)** |

위치는 다 (5,5) 동일, 색은 입력색을 따라감. ← Slice 2 핵심.

### 구현이 재현해야 할 시퀀스
```
[TASK]   형제 없음 → 비교 0 → intra-descend
[PAIR]   Inter-Pair(grid-count): P0,P1 COMM / Pa DIFF(출력 가려짐). 목표: Pa 출력 → 막힘 → descend
[GRID]   Inter-Pair-Grid(role==G1): compare(P0.G1,P1.G1)=DIFF, COMM=[size] 뿐.
         "출력 고정 아님"(color/contents DIFF) → Slice-1 결정 실패 → 막힘 → intra-descend
[OBJECT] G1 의 객체로 내려감 (lazy extract).
         ① Inter-Pair-Object (role==G1 객체): 위치(5,5) COMM, 색 DIFF
         ② Intra-Pair-Object (한 pair 의 G0객체 ↔ G1객체): 색 COMM(보존), 위치 DIFF
         → 결정적: 위치 = COMM 고정 (5,5),  색 = G0 객체색 (P5)
         anti-unify: 출력객체 = { pos=(5,5) const, color=?c | ?c = G0.obj.color }
[PREDICT] test G0 객체색=4 → coloring(make_grid(6×6, 0), (5,5), 4)
[OUT]    K: (5,5)=4 제출
```

**결정적 비교**: Inter-Object(위치 COMM) + Intra-Object(색 보존)가 *함께* 답을 정한다.
Slice 1 과 달리 단일 COMM 이 아니라 **COMM 구조 + G0-출처 변수** 의 합성.

---

## 5. 모듈 범위

**IN (Slice 2 신규·확장)**:
- **D 객체 property** — `objects-of(grid)`, `color-of(obj)`, `position-of(obj)` (object.to_json 노출). lazy object extract 재활성 (OBJECT 하강 시에만).
- **A descent 확장** — GRID 부분-COMM 시 OBJECT 로. `LEVELS += OBJECT`, `MAX_SUBSTATE_DEPTH` 3 으로.
- **C intra 결정적** — intra-pair object 비교(색 보존) + inter-pair object(위치 COMM).
- **anti-unification** — per-pair 산물 → schema(const=COMM / var=DIFF, var 출처 추적). `program/anti_unification.py`(현 스텁) 최소 구현.
- **합성형 Predict** — `coloring(make_grid(size), pos=COMM, color=G0.obj.color)`. 씨앗 2개 *조합* 시작. schema 는 semantic DSL 라이브러리로 deposit.

**OUT (Slice 3+)**: 위치·크기가 *관계* 에서 (e=우하단/크기, f=크기-입력, g=크기-고정), 다중 객체, 다중 변수, coloring/make_grid 외 transformation(영구 금지), 일반 DSL composition search.

---

## 6. 모듈 정의 (확장분만)

### D — 객체 property (Slice 1 grid property 와 동형, object.to_json 노출)
```
util:      objects-of(grid)            # lazy: 없으면 extract_objects() 1회
property:  (object) color / position / size / ...  # object.to_json() 키 노출, 재계산 ✗
```

### A — descent 확장
```
LEVELS = [TASK, PAIR, GRID, OBJECT]    # OBJECT 추가
GRID 처리: Inter-Pair-Grid 가 *부분 COMM*(전부 COMM 아님)이면 → 막힘 → OBJECT 하강
OBJECT 처리(결정 조건): inter(위치류 COMM) + intra(보존된 property) 로 출력 구성 가능 → 결정적
```

### anti-unification (최소)
```
입력: example 별 (출력객체 property dict)  +  대응 G0 객체 property
COMM property → const,  DIFF property → 변수.  변수는 *같은 pair 의 G0* 에서 동일 값 찾으면 출처=G0
출력: schema = { const props, var props with source }   # = 새 고급 DSL (semantic 라이브러리)
```

### Predict (합성형) + K
```
schema + test.G0 → 변수값 채움(색=G0색) → coloring(make_grid(size,0), pos, color) → emit
```

---

## 7. 작업 순서 (모듈 단위 · 각 단계 후 멈춤)

### 단계 1 — D 객체 property + lazy object extract
- `objects-of`, `color-of(obj)`, `position-of(obj)`. OBJECT 하강 시 `extract_objects()` 1회.
- **멈춤**: easy000c 의 P0.G1 객체 = 위치 (5,5)·색 2 로 나오는지.

### 단계 2 — A descent GRID→OBJECT
- GRID Inter 가 부분 COMM(size만)이면 막힘 → OBJECT 하강. `MAX_SUBSTATE_DEPTH=3`.
- **멈춤**: easy000c 가 GRID 에서 *부분 COMM 으로 막혀* OBJECT(S4)로 내려가는지.

### 단계 3 — C intra 결정적 (색 보존) + inter (위치 COMM)
- intra-pair object(G0↔G1) 색 COMM, inter-pair object 위치 COMM.
- **멈춤**: "위치=COMM(5,5), 색=intra-preserved(G0)" 가 로그에 그대로.

### 단계 4 — anti-unification (schema 추출)
- P0/P1 에서 schema `{pos=(5,5) const, color=var←G0}` 추출, 두 example 에서 일관.
- **멈춤**: schema 가 P0·P1 양쪽과 모순 없는지 (anti-unify 건전성).

### 단계 5 — 합성형 Predict + K
- test G0색=4 → `coloring(make_grid, (5,5), 4)` → emit. (씨앗 2개 조합 첫 발현)
- **멈춤**: easy000c 정답 `(5,5)=4` (env reward 1.0).

### 단계 6 — easy000d 회귀 (위치 (1,2))
- 같은 코드로 easy000d (위치 1,2) → 정답. 위치·색 agnostic 검증.
- **멈춤**: c·d 둘 다 통과 + 4 관찰 기준.

---

## 8. 각 멈춤에서 보고할 것 (Slice 1 §8 그대로)

- 무엇을 만들었나 (파일·함수) / easy000c 에서 어디서 어떻게 호출되는가 (trace)
- 4 관찰 기준 자가 점검 / 막힌·애매한 결정 — 사용자 판단 요청

---

## 9. Slice 2 통과 후

`easy000c` + `easy000d` 둘 다 정답 + 4 관찰 기준 → Slice 2 완료.
다음 Slice 3 (e·f·g): 위치·크기가 *관계* 에서 도출 (다중 변수, property 관계, 본격 DSL
composition·라이브러리 성장). 별도 가이드로 전환.
