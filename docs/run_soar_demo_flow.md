# run_soar_demo 실행 흐름 (업데이트 반영)

풀 문제 개수와 상관없이 **task가 없을 때까지** get_task → solve → step을 반복하고, 더 이상 task가 없으면 스스로 중지하는 구조다.

---

## 1. 진입: `main()`

```
1. task_list 결정
   - SOLVER_TASK_IDS가 있으면 → 그 목록 (1개, 10개, 100개 등 상관없음)
   - 비어 있거나 None이면 → None (환경이 가진 전체 문제 사용)

2. env = ARCEnvironment(task_list=task_list)
   - 풀 문제 집합만 정함. 개수는 몰라도 됨.

3. agent = SoarDemoAgent(verbose=..., soar_max_steps=50)

4. result = env.run_benchmark(agent, n=None)
   - "한 문제만" 호출하지 않음.
   - 환경에서 task를 받아 올 때까지 반복하다가, task가 없으면 종료.

5. correct / total 및 results 일부 출력
```

---

## 2. 환경: `run_benchmark(agent, n=None)`

진행 순서는 아래와 같다.

```
1. episode_list = _task_ids[:n] (n=None이면 전부)
   - 비어 있으면 → {"correct":0, "total":0, ...} 반환 후 끝.

2. self.reset(task_list=episode_list)
   - _episode_task_ids = episode_list
   - _current_index = -1, _done = (목록 비어 있으면 True)
   - 시간 예산 있으면 여기서 체크 후 _done 설정 가능
   - 첫 task로 이동: _advance_to_next_task() → 첫 task JSON 반환 (없으면 None)

3. while not self._done:
   ┌─────────────────────────────────────────────────────────────┐
   │ 3.1 task = self.get_task()                                   │
   │     - None이면 break → 루프 종료 (풀 문제 없음 → 스스로 중지)  │
   │                                                               │
   │ 3.2 task_id = get_current_task_id()  (로깅/결과용)           │
   │                                                               │
   │ 3.3 [같은 task에 대한 제출 루프]                              │
   │     step_info = None, num_submissions = 0                     │
   │     while True:                                               │
   │         answer = agent.solve(task, step_info=step_info)       │
   │         reward, next_task, done, info = self.step(answer)     │
   │         num_submissions += 1                                  │
   │         step_info = { ... info, submission_index ... }         │
   │         if reward >= 1.0: correct += 1                        │
   │         agent.update_memory(reward)  (있으면)                  │
   │         if reward >= 1.0 or not can_retry: break              │
   │         task = self.get_task()  (재제출 시 같은 task 유지)    │
   │         if task is None: break                                │
   │     results.append({ task_id, reward, num_submissions, ... }) │
   │                                                               │
   │ 3.4 다음 반복에서 get_task()가 다음 task를 반환                │
   │     - 다음이 없으면 _advance_to_next_task()가 None 반환       │
   │     - get_task()가 None → break → while not _done 종료        │
   └─────────────────────────────────────────────────────────────┘

4. return { "correct", "total", "results", "trace" }
```

- **task가 없을 때까지** 계속 도는 것은 `while not self._done` + `task = self.get_task()`이고, `get_task()`가 내부적으로 `_advance_to_next_task()`를 쓰며, 인덱스가 끝나면 `_done=True`, 다음 `get_task()`가 None을 주면서 break로 스스로 중지한다.

---

## 3. 정답이 “제출”되는 시점 (한 문제당 3회 제한과의 관계)

- **제출이 일어나는 곳**: 환경의 `run_benchmark` 안에서, **`answer = agent.solve(task, step_info)` 다음에 오는 `self.step(answer)`** 가 호출될 때마다 **1회 제출**로 카운트된다.
- 즉, **`solve()`가 반환할 때마다 그 반환값이 곧바로 `step(answer)`로 넘어가서 제출**된다. “제출을 미루거나, 확신 날 때만 제출”하는 별도 단계는 없다.
- 따라서:
  - **solve() 한 번 호출 = 제출 1회**.
  - 첫 번째 제출이 틀리면 `can_retry`로 같은 task로 다시 `solve()` → `step()` (2회 제출).
  - 또 틀리면 한 번 더 (3회 제출). 그 후에는 `can_retry`가 False가 되어 해당 task는 종료.
- **현재 구조에서는 “신중하게 한 번만 제출”하는 로직이 없다.** 에이전트가 `solve()`에서 반환하는 답이 그대로 매번 제출되므로, **제출을 신중하게 하려면 `solve()` 내부에서 “확신 있을 때만 답을 채워서 반환”하도록 바꾸거나, 제출 횟수를 쓰지 않고 “연습만”하는 단계를 별도로 두는 식의 설계가 필요**하다.

---

## 4. 에이전트: `SoarDemoAgent.solve(task)` (한 번의 “풀기”) — 자세히

환경이 한 task를 넘길 때마다 **한 번** 호출되고, **그 반환값이 곧 그번 제출 답**이 된다. 내부 흐름은 아래와 같다.

### 4.1 입력·출력

- **입력**: `task` (환경이 준 문제 JSON), `step_info` (재제출 시 이전 채점 정보 등).
- **출력**: `answers` — test 순서대로의 출력 그리드 리스트 `[ grid0, grid1, ... ]`. 이게 **그대로 `step(answer)`에 넘어가서 1회 제출**로 사용된다.

### 4.2 단계별 흐름

```
[1] WM 초기화
    _build_wm_from_task(task)
    → goal, task, focus="TASK", deficits=[ ("GRID","contents","output-test-0"), ... ], found={}, tried=[]
    → “이 task의 test 출력을 채워야 한다”는 결핍만 세팅. 아직 답은 없음.

[2] SOAR 사이클 (run_cycle)
    - 최대 50스텝 또는 goal_satisfied / impasse 될 때까지 반복.
    - 매 스텝:
      (a) goal_satisfied(wm)? → wm.found에 output_test_0, output_test_1, … 전부 있으면 여기서 종료.
      (b) propose: WM을 보고 조건 맞는 연산자들 제안 (submit-answer, explore, set-exploration-target 등).
      (c) select: 선호 순서대로 하나 선택 (submit-answer 우선).
      (d) apply: 선택된 연산자의 effect(wm) 실행 → wm.apply_effect(...) 로 WM 갱신.
           - submit-answer: solver로 “답 만들기” 시도 → 성공하면 wm.found에 output_test_i 넣고 deficit 제거.
           - set-exploration-target: 탐색할 scope 설정 (예: INTER_PAIR GRID).
           - explore: 그 scope에 대한 탐색 실행, 필요 시 submit-answer 재시도 가능하도록 tried 정리.
      (e) on_after_apply (verbose면 로그).
    - 결과: wm.found / wm.deficits / wm.focus 등이 “풀어본 내용”으로 갱신됨. 답이 나왔으면 wm.found에 들어 있음.

[3] WM에서 답만 꺼내기
    answers = _answers_from_wm(wm)
    → [ wm.found.get("output_test_0"), wm.found.get("output_test_1"), ... ]
    → SOAR로 채운 건 그대로, 못 채운 test 자리는 None.

[4] 빈 자리 보완 (SOAR만으로는 부족할 때)
    missing = [ i for i, a in enumerate(answers) if a is None ]
    if missing:
        fallback = self._solver_agent.solve(task, step_info=step_info)  # 기존 SolverAgent로 전체 풀기
        for i in missing:
            answers[i] = fallback[i]   # 빈 자리만 채움
    → SOAR가 못 채운 test 출력만 SolverAgent 결과로 대체. 나머지는 WM 결과 유지.

[5] 반환
    return answers
    → 이 리스트가 run_benchmark 쪽에서 step(answer)로 넘어가서 “이번 제출”로 사용됨.
```

### 4.3 요약

- **solve() 한 번** = WM으로 SOAR 사이클 돌리기 → WM.found에서 답 수집 → 부족분만 SolverAgent로 채우기 → **그 리스트를 반환**.
- 반환된 리스트는 **호출 직후 `step(answer)`에 그대로 넘어가서, 그 시점에 1회 제출**된다. 즉, “풀기”와 “제출”이 분리되어 있지 않고, **풀기가 끝나면 곧바로 그 결과가 제출**되는 구조다.

---

## 5. 전체 흐름 요약 (데이터 흐름)

```
main()
  │
  ├─ task_list = SOLVER_TASK_IDS or None
  ├─ env = ARCEnvironment(task_list=task_list)
  ├─ agent = SoarDemoAgent(...)
  │
  └─ result = env.run_benchmark(agent, n=None)
        │
        ├─ reset(episode_list)  → 첫 task로 준비
        │
        └─ while not _done:
              │
              ├─ task = get_task()
              │     └─ None → break (풀 문제 없음 → 여기서 스스로 중지)
              │
              ├─ [같은 task에 대해] 반복:
              │     answer = agent.solve(task, step_info)
              │           │
              │           ├─ WM 구성 → run_cycle (submit-answer / explore / set-exploration-target)
              │           └─ WM.found + 부족분 SolverAgent로 보완 → return answers
              │     step(answer)  → 채점, can_retry 등
              │     update_memory(reward)
              │     맞거나 can_retry 끝나면 break
              │
              ├─ results에 이 task 결과 추가
              │
              └─ 다음 iteration에서 get_task() → 다음 task 또는 None
                    └─ None이면 break → run_benchmark 반환
        │
        └─ return { correct, total, results, trace }

  └─ correct/total 및 results 일부 출력
```

---

## 6. 정리

| 항목 | 내용 |
|------|------|
| **실행 단위** | “한 문제”가 아니라 **풀 문제가 없을 때까지** 반복. |
| **개수** | 1문제/10문제/100문제/전체 모두 동일한 흐름. |
| **중지 조건** | `get_task()`가 None을 반환할 때 (다음 task 없음). |
| **문제 목록** | `SOLVER_TASK_IDS` 또는 None(전체). 이름으로 주는 것은 그대로. |

이 문서는 위 업데이트 이후의 `run_soar_demo` 실행 흐름을 담고 있다.
