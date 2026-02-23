# 목적·절차 흐름 (TASK 수신 → 추상화까지)

이 문서는 TASK 수신부터 공통 transition 추상화까지의 **목적성**과 **절차**를 단계별로 정리한 것이다.

---

## 1. TASK 수신 → 목적 세우기

- **입력**: TASK. 그 안에 example pair(들)과 test pair가 있음.
- **관찰**: Test pair 안 내용물의 개수·구조(예: grid가 1개뿐)를 보면 example과 다르다는 것을 알 수 있음.
- **목적 설정**: 이 차이를 이용해 목적을 세움.  
  예: “grid를 만들어야 한다” → **test pair의 output grid를 만드는 것**이 목적.

---

## 2. “어떤 그리드를 만들어야 하는지”를 모름

- Pair끼리 **같은 그리드가 하나라도** 있으면, 그걸 참고할 수 있음.
- **문제**: Pair마다 그리드가 **다 다르면**, “어떤 그리드가 정답인지”는 그리드만 보고는 알 수 없음.
- **결론**: 그리드 자체만으로는 test output을 정할 **근거가 없음**.

---

## 3. “뭔가 같아야 한다” → transition

- 다 다르기 때문에, **“뭔가라도 같아야** test pair의 output grid를 만드는 것과 연결할 수 있다”는 방향을 찾음.
- 그 **“뭔가”**가 **transition**이라는 개념임.  
  (transition이라는 심볼이 없어도, “input을 output으로 바꾸는 것”이 같아야 한다는 요구는 세울 수 있음.)
- **추가 목적**: **Transition이라도 같아야** test output을 그 transition으로 만들 수 있다.

---

## 4. Transition을 찾기 위해 pair 하나로 들어감

- **목표**: 위 목적(transition 찾기)으로 **pair 하나**(예: pair0, train pair)를 잡고 들어감.
- **pair 내부**: 두 개의 grid — `input_grid`, `output_grid`.
- **절차**:
  1. 이 두 grid를 **비교**하고,
  2. 필요하면 **object·pixel 단위**까지 비교하는 작업에 들어감.
  3. 비교 결과와 규칙에 기반해 **pair0의 pair program**을 생성함.
- **의미**: 이게 **pair0의 transition 후보**임.

---

## 5. 다음 pair로 넘어감

- **다음 pair**(예: pair1)로 넘어감.
- **자연스러운 시도**: 이전 pair의 pair program을 transition으로 그대로 써 봄.
- **결과**: 그대로는 안 맞음 (pair1 input에선 다른 output이 나오거나 실패).
- **따라서**: **추상화**해서 **공통된 program(transition)**을 찾는 작업으로 이어짐.

---

## 6. 두 번째 pair로 넘어갈 때의 두 가지 방향 (A vs B)

| 방식 | 설명 |
|------|------|
| **A** | Pair1에 대해서도 **pair1 전용 pair program을 먼저** 만든다. 그다음 **pair0 program과 pair1 program을 anti-unify**해서 공통 transition을 찾는다. |
| **B** | Pair1의 input_grid, output_grid(및 grid→object→pixel 등)를 **pair0의 항목들과 비교해 나가면서**, 그 비교 흐름 **안에서** program을 만든다. (pair0와의 대응을 보면서 만듦.) |

- **요약**:  
  - **A**: pair1 program을 “pair1만 보고” 만든 뒤, 나중에 pair0와 합침.  
  - **B**: pair1을 볼 때부터 pair0와의 비교를 하면서, 그 비교에 맞춰 program을 만듦.

---

## 7. 선택: A를 먼저 하되, 직후 PAIR component 비교 → 그다음 추상화

- **선택**: **A**를 사용한다.
- **절차**:
  1. **A**: Pair1에 대해 pair1 전용 pair program을 **먼저** 생성·저장.
  2. **직후**: **PAIR component 간 비교** 수행.  
     (pair0의 component들 vs pair1의 component들 — 예: pair0 input_grid vs pair1 input_grid, pair0 output_grid vs pair1 output_grid 등. “어떤 것이 서로 대응하는지” 매칭 정보를 얻음.)
  3. **이후**: **추상화** 수행.  
     - **입력**: pair program0 + pair program1 (이 둘을 anti-unify하여 추상 프로그램 1개 생성).  
     - **보조**: PAIR component 비교 결과는 **프로그램이 아닌** 매칭 정보이므로, 추상화의 **보조 정보**로만 사용(term 정렬, step–component 해석 등).

---

## 8. 전체 절차 요약 (순서)

| 단계 | 절차 |
|------|------|
| 1 | TASK 수신. 목적: test pair의 output grid를 만드는 것. |
| 2 | “그리드만으로는 정답을 정할 수 없음” → “뭔가 같아야 한다”로 전환. |
| 3 | 그 “뭔가”를 **transition**으로 정의. 목적: transition이라도 같아야 test output을 만들 수 있음. |
| 4 | Pair0 진입. PAIR 내 input_grid vs output_grid 비교, 필요 시 object·pixel 비교. 비교·규칙으로 **pair0 pair program** 생성. (pair0 transition 후보) |
| 5 | Pair1로 넘어감. pair0 program 그대로는 안 맞음 → **추상화**로 공통 transition 찾기. |
| 6 | **A** 채택: pair1 전용 **pair1 pair program**을 먼저 생성·저장. |
| 7 | **직후** pair0–pair1 **PAIR component 비교** 수행. (매칭 정보 저장) |
| 8 | **이후** pair program0 + pair program1으로 **추상화**(anti-unify). PAIR component 비교 결과는 보조 정보로만 사용. |

---

이 문서는 “목적성 흐름”과 “다음 pair로 넘어갈 때 A 선택 + 직후 component 비교 + 추상화”를 하나의 절차로 이어서 정리한 것이다.
