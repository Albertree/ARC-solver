#!/usr/bin/env python3
"""
ARCEnvironment + SolverAgent: solver_main 흐름을 에이전트로 돌린다.
- 원하는 문제만 넣어서 디버깅하려면 SOLVER_TASK_IDS 를 설정.
"""

from arc_env import ARCEnvironment, SolverAgent

# 디버깅 시 테스트할 문제만 지정. None이면 easy 1개만.
# SOLVER_TASK_IDS = ["easy0016"]  # 예: ["easy0004"] 또는 ["easy0004", "easy0012"]
SOLVER_TASK_IDS = ["08ed6ac7"]  

# 에이전트 중간 출력: True면 단계별 로그 + 그리드 요약을 stdout에 출력.
VERBOSE = True


def main():
    if SOLVER_TASK_IDS is not None:
        task_list = SOLVER_TASK_IDS
    else:
        task_list = ["easy0016"]

    print(f"[run_env_solver] task_list = {task_list}")
    env = ARCEnvironment(task_list=task_list)

    # verbose=True: 단계별 로그 및 중간/최종 그리드 요약 출력
    # on_step: 각 단계마다 (step_name, data) 콜백 호출 → 로그 파일 저장 등에 활용
    def my_on_step(step_name: str, data: dict):
        if "grid" in data and data["grid"]:
            # 예: 중간 그리드를 파일로 저장하고 싶다면
            # with open(f"outputs/agent_{data.get('task_id','')}_{step_name}.json", "w") as f: ...
            pass

    agent = SolverAgent(verbose=VERBOSE, on_step=my_on_step)

    # 단일 task로 한 번 풀기
    reward, info = env.run_single_task(task_list[0], agent=agent)
    print(f"  task_id = {info.get('task_id')}, reward = {reward}, correct = {info.get('correct')}")

    # 벤치마크로 돌리려면:
    # summary = env.run_benchmark(agent, n=2)
    # print(summary)


if __name__ == "__main__":
    main()
