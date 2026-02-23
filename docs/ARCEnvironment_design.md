# ARCEnvironment 설계

에이전트(ARCKG)와 분리된 평가 환경. LLM/딥러닝 없이 순수 심볼릭 에이전트가 ARC-AGI 문제를 agentic하게 풀 수 있도록 task 제공·채점·시간 예산·trace를 담당한다.

## 역할 분리

| 구분 | 담당 |
|------|------|
| **ARCEnvironment** | task 순차 제공, answer 채점, 시간 예산, trace 기록 |
| **에이전트 (ARCKG 등)** | perception → deliberation → action (`solve(task)`), `update_memory(reward)` |

## 인터페이스

- **`env.reset(task_list=None)`**  
  새 에피소드 시작. `task_list`가 있으면 이번 에피소드에만 해당 목록 사용.  
  반환: 첫 번째 task의 JSON 또는 None.

- **`env.get_task()`**  
  현재 task JSON: `{"task_id": str, "train": [...], "test": [...]}`.  
  에피소드 종료 후에는 None.

- **`env.step(answer)`**  
  채점 후 `(reward, next_task, done)` 반환.  
  - `answer`: test pair 순서와 동일한 길이의 출력 그리드 목록 `[list[list[int]], ...]` (단일 그리드면 `[grid]` 한 개만 넘겨도 됨).  
  - `reward`: 1.0 = 전부 맞음, 0.0 = 하나라도 틀림.  
  - `next_task`: 다음 task JSON 또는 None.  
  - `done`: 에피소드 종료 여부.

- **`env.run_single_task(task_id, agent=None)`**  
  특정 문제만 테스트. `agent`가 있으면 `agent.solve(task)` 호출 후 채점해 `(reward, info)` 반환.

- **`env.run_benchmark(agent, n=None)`**  
  전체(또는 최대 `n`개) task에 대해 reset → get_task → agent.solve → step → agent.update_memory 반복.  
  반환: `{"correct", "total", "results", "trace"}`.

- **trace**  
  - `env.get_trace()`: 현재 에피소드 trace 목록.  
  - `env.save_trace(path)`: JSON 파일로 저장.

## 에이전트 루프 (권장)

```python
env = ARCEnvironment(task_list=["easy0001", "easy0004"])
agent = MyAgent()  # solve(task) -> answer, update_memory(reward)
first = env.reset()
while not env._done:
    task = env.get_task()
    if task is None:
        break
    answer = agent.solve(task)
    reward, next_task, done = env.step(answer)
    agent.update_memory(reward)
```

## 채점 규칙

- 각 test pair에 대해 에이전트가 제출한 출력 그리드와 GT를 **픽셀 완전 일치**로 비교.
- 모든 test pair가 맞으면 reward 1.0, 하나라도 다르면 0.0.
- `answer` 길이가 test pair 수와 다르면 0.0.

## 시간 예산

- `ARCEnvironment(time_budget_sec=300)` 처럼 생성 시 지정.
- `reset()` 시점부터 누적 시간이 예산을 넘으면 다음 `step()` 또는 `_advance_to_next_task()`에서 에피소드 종료.

## 파일 구조

- `env/arc_environment.py`: `ARCEnvironment`.
- `env/solver_agent.py`: `SolverAgent` (solver_main 흐름 에이전트).
- `env/__init__.py`: `ARCEnvironment`, `SolverAgent` export.
- `run_env_solver.py`: 환경 + SolverAgent로 단일 task 또는 벤치마크 실행.
