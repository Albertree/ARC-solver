# SOAR 스타일 인지 아키텍처로 ARC 솔버 설계

결핍 주도 탐색 계획과는 별도로, 솔버를 **SOAR(State, Operator And Result)** 인지 아키텍처처럼 구성할 수 있는지, 그리고 그렇게 하면 어떤 이점이 있는지 정리한다.

---

## 1. SOAR 핵심 개념 (요약)

- **Working Memory (작업 기억)**: 현재 상황을 나타내는 **상태**의 집합. 목표, 지각 입력, 중간 결과, 지금 풀고 있는 하위 문제 등이 심볼로 유지된다.
- **Operators (연산자)**: 상태를 바꾸는 행동. 각 연산자는 **조건(precondition)** 과 **효과(effect)** 를 가진다. “조건이 만족될 때만 제안된다.”
- **Decision Cycle (결정 사이클)**:
  1. **Propose**: 현재 상태와 목표에 맞는 연산자들을 **제안** (production rules / 조건 매칭).
  2. **Select**: 제안된 연산자 중 **하나를 선택** (선호도, 랜덤, 정책 등).
  3. **Apply**: 선택된 연산자를 **적용** → 작업 기억이 갱신됨.
  4. 목표 달성 또는 종료 조건이면 끝; 아니면 1로 돌아감.
- **Impasses (교착)**: “선택할 연산자가 없음” 또는 “여러 개인데 선호가 없음”이면 **impasse**가 발생. SOAR는 이를 해결하기 위해 **하위 목표(subgoal)** 를 만들고, 그 안에서 다시 propose–select–apply를 반복한다. → **계층적 문제 해결**이 자연스럽게 나온다.
- **Chunking (선택)**: 하위 목표가 해결되면 그 과정을 **새 규칙(chunk)** 으로 학습해, 다음에는 같은 상황에서 바로 적용할 수 있게 한다.

---

## 2. ARC 솔버를 SOAR처럼 보는 방법

### 2.0 SOAR Working Memory — 핵심 요약 및 ARC 매핑

#### WME (Working Memory Element)

- Working Memory는 **WME의 순서 없는 집합(unordered set)** 이다.
- 각 WME는 **트리플릿**: (identifier, attribute, value).

#### Identifier

- SOAR는 런타임에 심볼을 생성: **S1**(state), **O1**(operator), **A1**(일반 객체) 등.
- **State = Goal**: S1 자체가 top-level goal context.
- Subgoal 생성 시 **S2, S3 …** 가 자동 추가되고, **^superstate** 로 상위 state와 연결됨.
- **ARC 매핑**: 루트 state = **S1**. Impasse 시 **S2**를 추가하고 (S2 ^superstate S1)으로 연결하며, resolution 시 S2 WME만 제거. (2.0.1 보충 요약 참고.)

#### Attribute

- SOAR에서는 항상 **^** 접두사. 엣지 이름 역할.
- **SOAR 예약**: ^superstate, ^type, ^impasse, ^operator, ^io, ^input-link, ^output-link, ^item, ^quiescence 등.
- **사용자 정의**: 도메인에 맞게 자유 네이밍.
- **ARC**: ^goal, ^focus, ^deficit, ^tried, ^subgoal, ^operator, ^impasse, ^type 등.

#### Value

- **Identifier**: 다른 객체로의 포인터 → 그래프 엣지.
- **Symbolic constant**: move-forward, red (따옴표 없음).
- **String constant**: "move-forward" (따옴표 있음).
- **Integer / Float**: 6, 3.14.

#### Preference (연산자 선택 투표)

SOAR는 연산자 후보에 대해 선호도를 부여한다. 우리 구현에서는 **고정 순서(PREFERENCE_ORDER)** 로 “첫 번째 일치 = Best”에 해당한다.

| 심볼 | 의미 | 우리 구현 |
|------|------|-----------|
| + | Acceptable | 제안된 연산자 목록에 포함 |
| > | Best | PREFERENCE_ORDER에서 먼저 나오는 것 |
| ~ | Prohibit | 조건 불만족으로 제안 안 됨 |

#### Impasse 종류 및 Subgoal

| Impasse | 의미 | 우리 구현 |
|---------|------|-----------|
| **tie** | 여러 operator 경쟁, 우열 없음 | (미사용) |
| **no-change** | operator 선택됐으나 실행 정보 부족 | 연산자 없음 / 선택 불가 시 |
| **conflict** | require 충돌 등 | (미사용) |

→ Impasse 시 SOAR는 하위 State(S2…)를 자동 생성. 우리는 **S2**를 push해 (S2 ^superstate S1), (S2 ^impasse no-change)를 두고, decision cycle은 bottom state(S2)에서 동작; 해결 시 S2 WME 제거(pop).

#### ARC 솔버 WME 설계 (S1 기준)

| WME | 설명 |
|-----|------|
| (S1 ^type state) | State 객체 타입 (SOAR 예약 개념 반영) |
| (S1 ^goal *value*) | 최상위 목표. value = ("produce-output", task_id) |
| (S1 ^task-id *task_id*) | 현재 task 식별자. task 본문은 별도 보관. |
| (S1 ^focus *value*) | 현재 탐색 범위. "TASK" 또는 ("INTER_PAIR","GRID") 등. |
| (S1 ^deficit *tuple*) | 결핍. (level, attribute, context). 다중 값 가능. |
| (S1 ^output-test-*i* *grid*) | 찾은 출력. |
| (S1 ^tried *op_name*) | 시도한 연산자. 다중 값. |
| (S1 ^operator *op_name*) | **현재 선택/적용된 연산자** (사이클마다 갱신) |
| (S1 ^impasse *type*) | Impasse 발생 시: no-change 등. 해소 시 제거. |
| (S1 ^subgoal *value*) | 하위 목표. ("resolve-impasse",) 등. |
| (S1 ^_targets_set *list*) | 탐색 대상 목록 (내부). |
| (S1 ^_explored_scopes *list*) | 탐색한 scope 목록 (내부). |

**저장 규칙**: WM은 WME 집합으로만 갱신. Propose/Select는 WM **읽기만**, Apply 시에만 WME 추가/삭제.

#### ARCKG와의 연결

- **TASK→PAIR→GRID→OBJECT→PIXEL** 계층 = SOAR의 identifier 체인 구조와 동형.
- 하나의 노드가 여러 하위를 참조 = SOAR **multi-valued slot** (같은 ^attribute에 여러 value).
- **Impasse-driven search** = SOAR no-change impasse → subgoal로 지식 공백 해소.

#### 2.0.1 SOAR Working Memory — 보충 요약 (State / Operator / Subgoal / Python)

**Subgoal과 Goal Stack 구조**

- **S1은 전체 태스크가 끝날 때까지 절대 사라지지 않음.**
- Impasse 발생 시 **S2가 S1 위에 추가**됨 (S1 소멸 아님). S1과 S2는 WM에 **동시에 존재**.
- 깊이 판단은 숫자(S1&lt;S2)가 아니라 **^superstate 체인**으로 함: (S2 ^superstate S1) → S1이 최상위(^superstate 없음).
- **SOAR decision cycle은 항상 ^superstate 체인의 가장 끝(bottom) state에서 작동.**
- 별도의 ^focus WME나 메커니즘은 없음. 구조 자체가 작동 지점을 결정.

**Subgoal 해결 과정**

- S2 안에서 production rule 발화 → 결과를 ^superstate 따라 **S1 쪽 WME에 직접 기록** 가능.
- **S2 ^quiescence t** 도달 → S2 전체 WME 소멸 → S1이 다시 작동 지점이 됨.
- 중첩 예: S1 (top, 항상 생존) → S2 (S1의 subgoal) → S3 (S2 안에서 또 impasse 시).

**Goal 명시 vs Stack 방식**

- **Stack 방식(SOAR 기본)**: impasse 발생 = goal 생성, resolution = goal 소멸 (자동). 생명주기가 impasse/resolution과 1:1로 묶여 개발자가 goal 소멸 조건을 별도로 코딩할 필요 없음 → 더 안정적.
- 명시적 goal 객체 방식은 goal 내용(what)은 표현 가능하나 생명주기를 직접 관리해야 해서 실수 가능.

**State란**

- "지금 세계가 어떤 상태인가"를 담는 **그릇**. 모든 WME의 **진입점(그래프 루트)**.
- 두 종류 정보: (1) 문제 맥락 정보(^name, ^step-count, ^wall-distance 등), (2) 현재 선택된 행동(^operator).

**Operator란**

- "state를 **어떻게 바꿀 것인가**"를 담는 객체. state에 ^operator로 연결되는 순간부터 존재, 실행 후 제거됨.
- **Operator 자체는 아무것도 안 함.** Production rule이 "이 operator가 선택돼 있으면 state를 이렇게 바꿔라"를 발화하면서 실제 변화가 일어남.
- 비유: State = 칠판, Operator = 뭘 쓸지 결정된 계획, Production rule = 실제로 분필을 드는 손.

**Identifier와 그래프 루트**

- 엄밀히는 O1, A1도 identifier 자리에 올 수 있음. 다만 **어떤 state로부터도 도달 불가능한 WME**는 어떤 rule도 찾아오지 않아 사실상 무의미 → State가 실질적인 그래프 루트 역할.

**Python 구현 스케치 (참고)**

- **WME**: identifier(State), attribute, value, preference(선택).
- **Operator**: id(O1, O2…), name, params, preference.
- **State**: id(S1, S2…), superstate(State | None), **slots: dict[str, list]** (multi-valued slot), proposed_operators, selected_operator, impasse_type, impasse_attribute.
- slots를 `dict[str, list]`로 하는 이유: 같은 attribute에 여러 value가 동시에 존재 가능(tie impasse 시 ^operator-candidate에 O1, O2 동시 존재). ARCKG에서 GRID→여러 OBJECT 참조와 동일한 패턴.

**ARCKG 연결 보충**

| SOAR | ARCKG |
|------|--------|
| ^superstate 체인 (S2 ^superstate S1) | TASK→PAIR→GRID→OBJECT→PIXEL 계층의 **부모 참조** |
| Impasse-driven subgoal 생성/소멸 | Knowledge gap 감지 → 하위 레벨 탐색 → 결과 반환 |
| Multi-valued slot (같은 ^attr에 여러 value) | 하나의 노드가 **여러 하위 노드**를 참조하는 일대다 관계 |

구현에서는 **state stack**을 두고, impasse 시 S2를 push하여 (S2 ^superstate S1), (S2 ^type state), (S2 ^impasse …)를 추가하고, resolution 시 S2 WME만 제거하고 pop한다. operator/impasse는 **현재(bottom) state**에 두고, goal/focus/deficits/found/tried는 S1에 유지해 Apply 결과가 항상 S1에 쌓이도록 할 수 있다.

### 2.1 Working Memory (상태)에 넣을 것

| 요소 | 설명 |
|------|------|
| **goal** | 최상위 목표. 예: `(produce-output, test-pair-0)` |
| **task** | 현재 TASK (example pairs, test pairs, 메타데이터) |
| **focus** | 지금 “어디를 보고 있는가”: 현재 PAIR 인덱스, 현재 GRID(입력/출력), 현재 레벨(TASK/PAIR/GRID/OBJECT/PIXEL) |
| **deficits** | 결핍 목록. 예: `[(GRID, contents, output-test-0), ...]` |
| **found** | 이미 얻은 정보: PaG1 후보, 비교 결과 요약, 추출한 rule 일부 등 |
| **tried** | 이미 시도한 연산자/탐색 (중복 방지, 백트랙 시 활용) |
| **subgoal** (impasse 시) | 현재 풀고 있는 하위 목표. 예: `(resolve-deficit, (GRID, contents, ...))` |

이렇게 하면 **결핍 주도 계획**의 “결핍 목록”, “현재 보는 범위”가 그대로 **상태**로 들어간다.

### 2.2 Working Memory는 어떻게 동작하는가

Working Memory(WM)는 **단일 진실 공급원**이다. 모든 “지금 무엇을 아는가 / 무엇이 부족한가”는 WM에만 있고, **읽기/쓰기**가 명확히 나뉜다.

#### (1) 누가 읽고 누가 쓴다

| 시점 / 주체 | WM에 대한 동작 |
|-------------|-----------------|
| **초기화** | TASK가 들어오면 WM을 **한 번** 채움: `goal`, `task`, `focus=TASK`, `deficits`(예: output을 만들 수 없으므로 “output grid의 size/color/contents” 등), `found={}`, `tried=[]`, `subgoal=None`. |
| **Propose** | WM을 **읽기만** 함. `goal`, `focus`, `deficits`, `found`, `tried`를 보고 “조건에 맞는 연산자” 목록을 만든다. WM은 바꾸지 않음. |
| **Select** | 제안된 연산자 목록(과 선호도)을 보고 **하나만** 고른다. WM을 바꾸지 않음. |
| **Apply** | 선택된 연산자를 실행하면서 **WM만** 수정함. 각 연산자의 effect에 따라 `deficits` 추가/제거, `found` 갱신, `focus` 이동, `tried`에 기록 등. |
| **Impasse 시** | WM에 `subgoal`을 **쓰고**, 그 하위 목표에 맞는 연산자만 다음 propose에서 고려. 하위 목표 해결 후 `subgoal`을 **지움**. |

즉, **WM을 쓰는 것은 “초기화”와 “연산자 Apply” 두 곳뿐**이다. 다른 코드가 WM을 직접 건드리지 않으면, “왜 이 상태가 됐는지”를 연산자 이력으로 추적할 수 있다.

#### (2) 한 사이클 안에서의 흐름

```
[현재 WM]  goal, task, focus, deficits, found, tried, subgoal
     │
     ▼
  Propose  ─── WM 읽기 ───► 적용 가능한 연산자 목록 O₁, O₂, ...
     │
     ▼
  Select   ─── 목록 + 선호도 ───► 선택된 연산자 O
     │
     ▼
  Apply(O) ─── O의 effect 실행 ───► WM 갱신 (deficits/found/focus/tried 등 변경)
     │
     ▼
  목표 달성? / 연산자 없음?  ─── Yes ───► 종료
     │ No
     └──────────────────────────────► 다시 Propose (위로)
```

매 사이클마다 **이전 WM 상태**로 propose → select → apply가 한 번 돌고, **다음 사이클의 WM**은 apply 결과뿐이다. 그래서 “한 스텝 전 상태”를 알면 “다음 상태”가 결정된다.

#### (3) 구체적인 갱신 예 (Apply 시)

- **`try-pag1` 적용 후**
  - 성공: `deficits`에서 `(GRID, contents, output-test-0)` 제거. `found["output_test_0"] = <예측 그리드>` 추가. `tried`에 `try-pag1` 추가.
  - 실패: `tried`에 `try-pag1`만 추가. `deficits`는 그대로 (다음에 `expand-scope-grids`나 `enter-object-level`이 제안됨).
- **`enter-pair(0)` 적용 후**
  - `focus`를 `(PAIR, 0)`으로 변경. `tried`에 `enter-pair-0` 추가. `deficits`/`found`는 연산자 설계에 따라 유지 또는 미세 조정.
- **`enter-object-level` 적용 후**
  - `focus`를 `(OBJECT, ...)`로 변경. `deficits`를 “grid contents” 대신 “object 단위로 쪼갠 결핍”으로 바꾸거나, 하위 목표로 넘길 수 있음.

이렇게 **연산자마다 “WM을 어떻게 바꿀지”를 effect로 고정**해 두면, Working Memory 동작이 예측 가능하고 재현 가능해진다.

#### (4) 정리

- Working Memory는 **항상 현재 상태 하나**만 유지하고, **Propose/Select에서는 읽기만**, **Apply(와 초기화)에서만 쓰기**가 일어난다.
- 동작은 **“초기 WM → [Propose → Select → Apply → (WM 갱신)] 반복 → 종료 조건”** 한 가지 흐름이다.
- 그래서 “어떤 결핍이 있었고, 무엇을 시도했고, 지금 어디를 보고 있는지”는 전부 WM만 보면 알 수 있다.

### 2.3 Operators (연산자) 예시

각 연산자는 “언제 제안되는가(precondition)”와 “무엇을 바꾸는가(effect)”로 정의한다.

| 연산자 | Precondition (제안 조건) | Effect (적용 시) |
|--------|--------------------------|-------------------|
| `compare-pair-properties` | goal = produce-output, focus = TASK, deficits에 PAIR 수준 결핍 가능 | PAIR들 property 비교 결과를 `found`에 넣음; focus는 그대로 또는 PAIR로 |
| `try-pag1` | deficits에 (GRID, contents, …) 있음, 아직 다른 grid 범위 확장 안 함 | 다른 pair의 grid 비교, test input 매칭 시도; 성공 시 해당 deficit 제거 및 output 후보를 `found`에 추가 |
| `enter-pair` | focus = TASK 또는 PAIR들만 봄, deficits에 grid/object 수준 결핍 있음 | focus를 한 PAIR(예: pair 0)으로 고정 |
| `compare-grids-within-pair` | focus = 한 PAIR, deficits에 (GRID, contents/…) 있음 | 그 PAIR의 input↔output grid 비교, rule 후보를 `found`에 추가 |
| `expand-scope-grids` | 같은 레벨에서 “다른 grid” 비교 아직 안 함, deficit = grid 속성 | 다른 grid / 다른 pair의 grid 비교 수행, `found` 갱신 |
| `enter-object-level` | deficit (GRID, contents)가 범위 확장으로 채워지지 않음 | focus를 OBJECT로, deficit를 object 단위로 쪼개거나 하위 목표로 전달 |
| `compare-objects-within-grid` | focus = 한 grid의 OBJECT | 그 grid 안 object들 간 비교, `found` 갱신 |
| `expand-scope-objects` | object 결핍, 아직 다른 grid/pair의 object 비교 안 함 | 다른 grid·다른 pair의 object 비교 |
| `enter-pixel-level` | object 수준으로도 결핍 해소 불가 | focus = PIXEL, 픽셀 단위 비교/rule 추출 |

“결핍 → 탐색” 테이블은 **연산자 제안 조건**으로 녹일 수 있다. 예: deficit가 `(GRID, contents)`이면 `try-pag1`, `expand-scope-grids`, `compare-grids-within-pair`, `enter-object-level` 중 조건을 만족하는 것만 propose된다.

### 2.4 Decision Cycle에 맞추기

1. **Propose**: 현재 (goal, task, focus, deficits, found, tried)에 대해, precondition을 만족하는 연산자들을 모두 제안.
2. **Select**: 제안된 연산자 중 하나 선택.  
   - 결핍 주도와 맞추려면: “같은 결핍에 대해 범위 확장 연산자 우선, 실패 이력 있으면 깊이 진입 연산자” 같은 **선호도**를 두면 됨.
3. **Apply**: 선택된 연산자 실행 → working memory 갱신 (deficits 감소, found 증가, focus 이동, tried 기록).
4. **종료 조건**: goal이 만족됐을 때 (test output 생성됨) 또는 더 이상 제안할 연산자 없음(또는 시도 다 함) → impasse 또는 실패 처리.

이렇게 하면 “고정된 순서의 파이프라인”이 아니라 **상태에 반응해서 연산자를 고르는** 구조가 된다.

### 2.5 Impasses와 Subgoal

- **연산자 없음**: 현재 상태에서 precondition을 만족하는 연산자가 하나도 없음 → impasse.  
  → 하위 목표 생성 예: `(resolve-deficit, d)` for deficit `d`. 이 하위 목표가 있으면 “d를 채우기 위한” 연산자만 제안하도록 조건을 넣을 수 있음.
- **선택 불가**: 여러 연산자가 제안됐는데 선호가 없음 → (선택 정책을 넣거나) impasse로 보고 “어떤 연산자를 쓸지 결정”을 하위 목표로 만들 수 있음.

Subgoal이 해결되면 working memory에서 해당 subgoal을 치우고, 상위 목표로 돌아가서 다시 propose–select–apply.  
원하면 나중에 **chunking**처럼 “이 subgoal + 이 상태 → 이 연산자”를 새 규칙으로 저장해, 다음에 비슷한 결핍이 나오면 바로 그 연산자를 제안하도록 할 수 있다.

---

## 3. 결핍 주도 계획과의 연결

- **결핍** = working memory의 `deficits` 리스트. “무엇이 비어 있는가”가 명시적으로 유지됨.
- **결핍 → 탐색 결정** = **연산자 제안 조건**.  
  예: deficit `(GRID, contents)` → `try-pag1`, `expand-scope-grids`, `enter-object-level` 등의 precondition에 “deficits에 (GRID, contents) 포함”이 들어감.  
  “먼저 범위 확장, 실패 시 깊이 진입”은 **선호도(preference)** 로 구현 (범위 확장 연산자에 더 높은 선호).
- **탐색 공간** = 제안 가능한 연산자들의 집합. SOAR의 “problem space”는 여기서 (goal, operators) 쌍으로 이해하면 됨.

즉, 결핍 주도 계획은 **상태(결핍) 기반으로 연산자를 제안·선택하는 SOAR 스타일**과 잘 맞고, “원하는 정보만 탐색”은 “필요한 연산자만 precondition에 의해 제안된다”로 보장할 수 있다.

---

## 4. 구현 시 유의점

- **Production rule 표현**: 연산자 제안을 “if (state matches) then propose operator” 형태로 두면, 기존 결핍→탐색 테이블을 그대로 규칙으로 옮기기 쉽다.
- **선택 정책**: SOAR는 보통 선호도(preference)로 선택. ARC에서는 “같은 deficit에 대해 범위 확장 > 깊이 진입”, “이미 tried에 있으면 제외” 등을 선호도/필터로 두면 됨.
- **상태 갱신**: 연산자 적용 시 `deficits`, `found`, `tried`, `focus`를 어떻게 바꿀지 각 연산자마다 명시. 디버깅과 재현이 쉬워진다.
- **점진적 도입**: 기존 `test()` 루프를 한 번에 바꾸지 말고, “상태 + 연산자 한 세트”만 SOAR 스타일로 두고, 결정 사이클은 기존 코드를 감싸는 형태로 시작해도 된다.

---

## 5. Long-Term Memory (LTM) 세 가지: 경로·역할·저장 내용

SOAR의 LTM은 **Procedural**, **Semantic**, **Episodic** 세 가지다. ARC 솔버에서는 현재 **Semantic에 해당하는 저장소만** `semantic_memory/` 경로에 존재한다. 나머지 둘은 **별도 폴더** `procedural_memory/`, `episodic_memory/`로 둔다.

### 5.1 전체 경로 구조

- **Semantic**: `semantic_memory/` (기존 `memory/` 이름 변경)
  - 노드·속성·비교 엣지: `semantic_memory/N_T{hex}/`, `semantic_memory/.../E_*.json`
- **Procedural**: `procedural_memory/`
- **Episodic**: `episodic_memory/`

세 종류를 각각 **폴더 이름으로 구분**해 두면, “장기 기억” 역할별로 경로가 명확해진다.

---

### 5.2 Semantic Memory (`semantic_memory/`)

**역할**: “무엇인가”, “어떤 관계인가” 같은 **선언적·개념적 지식**. 특정 에피소드나 시점에 묶이지 않는 사실.

**저장 위치**: `semantic_memory/` (`ARCKG/memory_paths.py`의 `MEMORY_ROOT` = `semantic_memory/`)

**저장되는 정보**:

| 종류 | 경로 예시 | 저장 내용 (어떤 정보) | 형식 |
|------|-----------|------------------------|------|
| 노드 구조 | `semantic_memory/N_T{hex}/`, `N_P{id}/`, `N_G{id}/`, `N_O{id}/`, `N_X{id}/` | TASK·PAIR·GRID·OBJECT·PIXEL 계층. 폴더 존재 자체가 “이 task에 이 노드가 있다”는 사실 | 디렉터리 |
| 노드 속성 (self-edge) | `semantic_memory/N_T{hex}/E_T{hex}.json`, `.../E_P{id}.json`, `.../E_G{id}.json` 등 | 해당 노드의 property: size, color, contents, 객체 수 등 | JSON |
| 비교 결과 (엣지) | `semantic_memory/N_T{hex}/E_{label1}-{label2}.json` (예: `E_P0G0-P1G0.json`) | 두 노드 간 비교 결과: score, symbolic distance, 공통/차이 요약 등 | JSON |

**동작**:  
- **쓰기**: compare·update_property 시 노드/엣지 경로에 JSON·디렉터리 생성.  
- **읽기**: Propose나 연산자 실행 시, “이 task의 이 노드/엣지가 있으면” 해당 경로에서 로드해 WM의 `found`나 비교 로직에 사용.

**정리**: Semantic = **`semantic_memory/` 전체**. “이 task의 구조·속성·비교 관계”가 시점 무관한 지식으로 저장된다.

---

### 5.3 Procedural Memory (`procedural_memory/`)

**역할**: “**어떤 조건일 때 어떤 행동을 할지**” 규칙. SOAR의 production rule / 스킬. “조건 → 연산자 제안/선택” 지식.

**저장 위치**: `procedural_memory/`

**저장되는 정보**:

| 파일/경로 | 저장 내용 (어떤 정보) | 형식 |
|-----------|------------------------|------|
| `procedural_memory/productions.json` (또는 규칙별 파일) | **Production rule 목록**. 각 규칙: (condition, action, preference). condition = WM 패턴 (goal, focus, deficits 타입, tried 여부 등). action = 연산자 이름 또는 ID. preference = 선택 시 우선순위 (예: scope-expansion > depth) | JSON 배열 또는 규칙당 JSON |
| (선택) `procedural_memory/chunks/` | Chunking으로 **학습된 규칙**. “이전 에피소드에서 subgoal 해결 시 쓴 (상태, 연산자)”를 새 규칙으로 저장. 나중에 같은 조건이면 이 규칙이 제안됨 | JSON (condition + action) |

**Condition 예시** (WM 패턴):

```json
{
  "goal_type": "produce-output",
  "deficit": ["GRID", "contents"],
  "tried_operators": { "exclude": ["try-pag1"] },
  "focus_level": "TASK"
}
```

**Action 예시**: `"try-pag1"`, `"expand-scope-grids"`, `"enter-object-level"`

**동작**:  
- **쓰기**: (1) 초기 규칙 세트를 `procedural_memory/productions.json` 등으로 배치. (2) Chunking 구현 시, subgoal 해결 후 새 규칙을 `procedural_memory/chunks/`에 추가.  
- **읽기**: **Propose 단계**에서 현재 WM을 condition에 대입해 매칭되는 규칙만 골라, 해당 action을 “제안된 연산자”로 씀. Select 시 preference 사용.

**정리**: Procedural = **“언제 어떤 연산자를 쓸지”** 규칙. 경로는 `procedural_memory/`, 내용은 condition → action (＋ preference), 형식은 JSON.

---

### 5.4 Episodic Memory (`episodic_memory/`)

**역할**: **과거 경험 한 건 한 건**. “언제, 어떤 task에서, 어떤 상태에서 어떤 연산자를 썼고 결과가 어땠는지” 같은 시점·맥락이 붙은 기록.

**저장 위치**: `episodic_memory/`

**저장되는 정보**:

| 경로 | 저장 내용 (어떤 정보) | 형식 |
|------|------------------------|------|
| `episodic_memory/by_task/{task_id}.json` (또는 `{task_id}_{run_id}.json`) | **한 번의 풀이 에피소드**: task_id, (선택) run_id/타임스탬프, WM 스냅샷 또는 state_id, 적용한 연산자 시퀀스, 각 단계 결과(성공/실패), 최종 outcome(성공/실패, reward) | JSON |
| (선택) `episodic_memory/index.json` | task_id → 최근 에피소드 파일 경로 또는 요약 (빠른 검색용) | JSON |

**에피소드 JSON 예시**:

```json
{
  "task_id": "08ed6ac7",
  "run_id": "20250315_001",
  "outcome": "success",
  "reward": 1.0,
  "steps": [
    { "wm_snapshot": { "focus": "TASK", "deficits": ["(GRID,contents,output-test-0)"] }, "operator": "try-pag1", "result": "fail" },
    { "wm_snapshot": { "focus": "PAIR", "pair_idx": 0 }, "operator": "compare-grids-within-pair", "result": "ok" },
    { "operator": "enter-object-level", "result": "ok" },
    ...
  ]
}
```

**동작**:  
- **쓰기**: Decision cycle이 한 스텝 돌 때마다 (또는 연산자 적용 시) step을 append. task 종료 시 outcome/reward 기록하고 `episodic_memory/by_task/{task_id}.json`(또는 run별 파일)에 저장.  
- **읽기**: (1) **재생(replay)**: 비슷한 task나 같은 task 재시도 시 과거 에피소드 로드해 “비슷한 상황에서 뭘 했는지” 참고. (2) **학습**: Chunking에 “이 에피소드에서 이 상태일 때 이 연산자가 성공했다”를 procedural로 옮길 때 사용. (3) **디버깅/분석**: 어떤 연산자 순서가 성공/실패했는지 추적.

**정리**: Episodic = **“무슨 일이 일어났는지”** 시계열. 경로는 `episodic_memory/`, 내용은 task별(또는 run별) (state, operator, result) 시퀀스와 최종 outcome, 형식은 JSON.

---

### 5.5 요약 표

| LTM 종류 | 경로 | 저장하는 것 | 언제 읽고 언제 씀 |
|----------|------|-------------|-------------------|
| **Semantic** | `semantic_memory/` (N_T, N_P, E_* 등) | 노드 구조·속성·비교 엣지 (무엇인가, 어떤 관계인가) | compare/property 갱신 시 씀; Propose·연산자 실행 시 읽음 |
| **Procedural** | `procedural_memory/` | 조건→연산자 규칙 (언제 무엇을 할지) | Propose 시 읽어서 연산자 제안; Chunking 시 새 규칙 씀 |
| **Episodic** | `episodic_memory/` | task별 풀이 에피소드 (무슨 일이 일어났는지) | 매 스텝/종료 시 씀; replay·학습·분석 시 읽음 |

이렇게 디자인하면 SOAR의 LTM 세 종류가 각각 **폴더 이름·역할·저장 정보·형식**이 명확히 나뉘고, Semantic은 `semantic_memory/`, Procedural·Episodic은 각각 별도 폴더로 둔다.

---

## 6. 구현 가이드: WM 클래스, Rule, Operator, Preference 생성

이걸 **만들 때** WM은 클래스로 두고, rule·operator·preference는 아래처럼 생성/구조화하면 된다.

### 6.1 Working Memory — 클래스로 두기

**이유**: 상태를 한 덩어리로 묶고, “읽기 전용 노출”과 “Apply 시에만 쓰기”를 메서드로 나누기 좋다.

**필드 (속성)**  
`goal`, `task`, `focus`, `deficits`, `found`, `tried`, `subgoal` — 문서 2.1과 동일.

**제안하는 인터페이스**:

- **생성자**  
  `WorkingMemory(goal=..., task=..., focus=..., deficits=..., found=..., tried=..., subgoal=...)`  
  초기화 시 한 번만 호출.
- **읽기**  
  규칙/선택기가 WM을 볼 때만 쓸 수 있게:  
  - 속성으로 직접 읽기 (예: `wm.focus`, `wm.deficits`)  
  - 또는 **규칙 매칭용**으로 `wm.to_matchable()` 같은 메서드로 dict/불변 스냅샷 반환 (선택).
- **쓰기 (Apply 전용)**  
  WM을 바꾸는 건 “연산자 effect” 한 경로만 두는 게 좋다.  
  - **방법 A**: `wm.apply_effect(effect: dict)`  
    - `effect` 예: `{"remove_deficit": (...), "add_found": {...}, "set_focus": ..., "add_tried": [...]}`  
    - WM 클래스가 이 dict를 해석해서 자신의 필드만 갱신.  
  - **방법 B**: `wm.apply_operator(operator)`  
    - 각 Operator가 `def effect(self, wm) -> None` 또는 `def effect(self, wm) -> dict` 로 “무엇을 바꿀지” 반환하고, WM이 그걸 적용.  
  - **방법 C**: Operator가 `get_effect(wm) -> dict` 만 반환하고, WM은 `apply_effect(dict)` 만 가짐.  
  → **권장**: B 또는 C. “effect = WM 갱신 내용”을 연산자 쪽에서 정의하고, WM은 “그걸 적용하는 책임”만 가지면 역할이 잘 나뉜다.
- **Subgoal**  
  impasse 시: `wm.set_subgoal(...)` 또는 `wm.apply_effect({"set_subgoal": ...})`.  
  해결 시: `wm.clear_subgoal()` 또는 `apply_effect({"set_subgoal": None})`.
- (선택) **복사**  
  규칙 매칭·에피소드 스냅샷용으로 `wm.copy()` 또는 `wm.fork()` 있으면 편하다.

**배치**: 예) `memory_system/working_memory.py` 또는 `soar/wm.py` 에 `WorkingMemory` 클래스 하나.

---

### 6.2 Operator — 어떻게 생성할지

**역할**: “이름 + 제안 조건(precondition) + 효과(effect)”를 한 단위로.

**생성 방식 두 가지**:

- **방식 1: 클래스 per 연산자**  
  - `BaseOperator`(또는 `Operator`) 추상 클래스:  
    - `name: str`  
    - `precondition(wm: WorkingMemory) -> bool`  
    - `effect(wm: WorkingMemory) -> dict` (또는 `effect(wm) -> None` 이고 WM 직접 수정).  
  - `TryPaG1`, `EnterObjectLevel` 등 구체 연산자는 이걸 상속해 precondition/effect만 구현.  
  - **장점**: 연산자별로 상태·로직이 복잡해져도 한 파일/클래스에 모을 수 있음.  
  - **단점**: 연산자 수가 많아지면 클래스 수가 늘어남.

- **방식 2: 연산자 레지스트리(딕셔너리) + 함수**  
  - `OPERATORS: dict[str, OperatorSpec]`  
  - `OperatorSpec` = `(precondition: Callable[[WM], bool], effect: Callable[[WM], dict])` 또는 dataclass.  
  - 연산자 이름을 키로, precondition/effect 함수를 값으로 등록.  
  - **장점**: 연산자 추가가 “한 줄 등록”으로 끝남.  
  - **단점**: precondition/effect가 길어지면 별도 함수로 빼야 해서, 결국 “이름 + 함수 둘”이 한 단위가 됨.

**권장**:  
- **Operator는 “이름 + precondition + effect” 한 묶음**으로 두고,  
- 구현은 **방식 2(레지스트리 + 함수)** 로 시작해,  
- 나중에 특정 연산자가 무거워지면 그만 **클래스(방식 1)** 로 분리해도 됨.

**effect 반환 형식**:  
- WM을 직접 수정하지 말고, **“변경 내용”만 dict로 반환**하게 하면 테스트·재현이 쉽다.  
  - 예: `{"remove_deficits": [d], "add_found": {"key": val}, "add_tried": ["try-pag1"], "set_focus": (PAIR, 0)}`  
- WM 클래스는 `apply_effect(effect_dict)` 로 이 dict만 해석해서 자신의 필드를 갱신.

**배치**: 예) `soar/operators.py` 또는 `memory_system/operators/` (연산자별 모듈 나누면 여기).

---

### 6.3 Rule (제안 규칙) — 어떻게 생성할지

**역할**: “WM이 이 조건을 만족하면, 이 연산자를 제안 목록에 넣는다.”

**생성 방식**:

- **ProductionRule** (또는 그냥 “규칙”) 하나당:  
  - **condition**: `(wm: WorkingMemory) -> bool`  
  - **operator_name**: `str` (연산자 레지스트리 키와 동일).  
- **Proposer** (제안기):  
  - 규칙 리스트를 가짐: `rules: list[ProductionRule]`.  
  - `propose(wm: WorkingMemory) -> list[str]`:  
    - 모든 규칙에 대해 `if rule.condition(wm): result.append(rule.operator_name)`  
    - 중복 제거(같은 연산자 이름이 여러 규칙에서 나올 수 있음).  
    - 반환: 제안된 연산자 **이름** 목록.

**규칙은 어디서 오는가**:

- **코드로 직접**:  
  - `rules = [ProductionRule(condition=lambda wm: ..., operator_name="try-pag1"), ...]`  
  - 또는 `def cond_try_pag1(wm): return ...` 처럼 함수로 두고 `ProductionRule(cond_try_pag1, "try-pag1")`.
- **설정(JSON/YAML)에서**:  
  - condition을 “WM 패턴”(dict)으로 저장해 두고, 인터프리터가 “wm.to_matchable()이 이 패턴을 만족하면 True”로 해석.  
  - 예: `{"deficits_contain": ["GRID", "contents"], "tried_excludes": ["try-pag1"]}` → 해당 조건일 때만 이 규칙의 operator_name 제안.  
  - **장점**: procedural_memory에 넣었다가 나중에 JSON에서 로드해 규칙 리스트로 복원하기 좋음.  
  - **단점**: 복잡한 조건은 패턴만으로 표현하기 어려우면, “특수 규칙만 코드(함수)”로 두고 나머지는 패턴.

**권장**:  
- **기본 규칙**은 코드에 `ProductionRule(condition_fn, operator_name)` 리스트로 두고,  
- **나중에 학습/추가되는 규칙**은 `procedural_memory/` JSON에서 읽어서 “패턴 + operator_name”을 규칙으로 추가.  
  - 패턴 매칭이 필요하면 `wm.to_matchable()` 이 WM을 dict(또는 JSON 가능한 구조)로 내려주고, 그걸 패턴과 비교하는 작은 매처를 두면 됨.

**배치**: 예) `soar/rules.py` 또는 `memory_system/productions.py`.  
규칙 리스트를 procedural_memory에서 로드하는 코드는 `memory_system/` 또는 `soar/` 한 곳에.

---

### 6.4 Preference (선호) — 어떻게 생성할지

**역할**: Propose가 반환한 연산자 이름 목록이 **여러 개**일 때, 그중 **하나**를 골라야 함. Preference가 “우선순위”를 정해 준다.

**생성 방식**:

- **방식 1: 고정 순서 리스트**  
  - `PREFERENCE_ORDER: list[str]` = `["try-pag1", "expand-scope-grids", "compare-grids-within-pair", "enter-object-level", ...]`  
  - `select(candidates: list[str])` = 후보 중 리스트에 **가장 먼저 나오는** 하나 반환.  
  - **장점**: 구현 단순.  
  - **단점**: 맥락(WM)과 무관하게 항상 같은 순서.

- **방식 2: (WM, 후보) → 하나**  
  - `select(wm: WorkingMemory, candidates: list[str]) -> str`  
  - WM 내용에 따라 선호를 바꿀 수 있음 (예: subgoal이 있으면 “subgoal 해결용” 연산자만 우선).  
  - **장점**: 결핍 종류·subgoal 유무에 따라 “범위 확장 먼저 / 깊이 진입 먼저”를 바꿀 수 있음.  
  - **단점**: 선택 로직을 한 곳에서 구현해야 함.

- **방식 3: 연산자별 선호도 점수**  
  - 각 연산자에 `preference_score(wm) -> float` (또는 정수) 부여.  
  - `select(wm, candidates)` = `max(candidates, key=lambda op: score(op, wm))`.  
  - **장점**: 연산자 추가 시 “점수만 주면” 됨.  
  - **단점**: 점수 함수를 어디서 정의할지, WM을 어떻게 쓰할지 정해야 함.

**권장**:  
- **먼저 방식 1(고정 순서)** 로 구현해 두고,  
- “같은 deficit인데 WM에 따라 순서를 바꾸고 싶다”는 요구가 생기면 **방식 2**로 `select(wm, candidates)` 를 도입.  
- 선호도 데이터를 procedural_memory에 두고 싶으면, “operator_name → priority” 맵을 JSON으로 저장하고, select 시 그 맵을 참조하면 됨.

**Impasse와의 관계**:  
- `select`가 **후보가 0개**이거나 **여러 개인데 동점**이면 “선택 불가”를 반환 (예: `None` 또는 특별한 토큰).  
- 그때 **impasse**로 보고 subgoal을 WM에 추가하고, 다음 사이클에서는 subgoal용 규칙만 propose되게 하면 된다.

**배치**: 예) `soar/preferences.py` 또는 `memory_system/selection.py`.

---

### 6.5 전체 조립 (결정 사이클)

1. **WM** = `WorkingMemory(...)` 인스턴스 하나.
2. **Propose** = 규칙 리스트 + 연산자 레지스트리(이름만 필요) → `proposer.propose(wm)` → `list[str]`.
3. **Select** = `preference.select(wm, candidates)` (또는 `select(candidates)`만) → `str | None`.
4. **Apply** = `operator = OPERATORS[selected]`, `effect = operator.effect(wm)` (또는 operator가 WM을 직접 수정), `wm.apply_effect(effect)`.
5. **Impasse**: `candidates` 비었거나 select가 None 반환 → `wm.set_subgoal(...)` 후 다음 사이클. Subgoal이 있으면 “subgoal용 규칙만” propose하도록 규칙 쪽에서 `wm.subgoal`을 보면 됨.
6. **종료**: goal 달성 시 또는 “제안도 없고 subgoal도 만들 수 없음”일 때.

이렇게 하면 **WM은 클래스 한 개**, **rule·operator·preference는 “생성/등록”만 잘 해 두면** impasses와 WM 관리가 위에서 말한 대로 동작하게 만들 수 있다.

---

## 7. 요약

- SOAR처럼 **Working Memory(상태) + Operators(연산자) + Decision Cycle(propose–select–apply)** 로 솔버를 만들 수 있다.
- **결핍**은 상태의 `deficits`로 두고, **“결핍이 무엇이기 때문에 어떤 것을 탐색한다”**는 **연산자 제안 조건(precondition)** 과 **선호도**로 구현하면, 결핍 주도 계획과 자연스럽게 맞는다.
- Impasses와 subgoal을 쓰면 “연산자 없음/선택 불가”일 때 하위 목표를 만들어 계층적으로 풀 수 있고, 원하면 chunking으로 비슷한 상황에서 재사용할 수 있다.
- **LTM**: Semantic = `semantic_memory/` (구조·속성·비교). Procedural = `procedural_memory/` (조건→연산자 규칙). Episodic = `episodic_memory/` (task별 풀이 에피소드). 각 경로에 무엇을 어떻게 저장할지 위 5절에 정리했다.
- **구현 시**: WM은 클래스로 두고, Rule은 condition + operator_name, Operator는 레지스트리 + (precondition, effect), Preference는 고정 순서 또는 select(wm, candidates). 위 6절에 생성·배치 방법을 정리했다.
- 계획(solver_flow_unification_plan.md)과는 별도 문서로 두었지만, **결핍 주도 탐색**을 **SOAR 스타일 아키텍처**로 구현하는 방향으로 정리해 두었다.
