"""
ARCEnvironment: 에이전트(ARCKG)와 분리된 평가 환경.
- ARC 데이터셋에서 task를 순차 제공, answer 채점, 시간 예산, trace 기록.
- LLM/딥러닝 없이 로컬 JSON 기반 메모리와 연동 가능.
"""

import inspect
import json
import time
from pathlib import Path
from typing import Any, Optional

from managers.arc_manager import ARCManager
from ARCKG.task import TASK

DEFAULT_MAX_ATTEMPTS_PER_PAIR = 3


def _solve_accepts_step_info(agent: Any) -> bool:
    """agent.solve가 step_info 키워드 인자를 받는지 여부."""
    if not hasattr(agent, "solve") or not callable(getattr(agent, "solve")):
        return False
    try:
        sig = inspect.signature(agent.solve)
        return "step_info" in sig.parameters
    except (ValueError, TypeError):
        return False


def _grids_equal(a: list, b: list) -> bool:
    """두 그리드(view: list[list[int]])가 완전히 같은지 비교."""
    if a is b:
        return True
    if len(a) != len(b):
        return False
    for row_a, row_b in zip(a, b):
        if len(row_a) != len(row_b) or row_a != row_b:
            return False
    return True


class ARCEnvironment:
    """
    에이전트에게 task를 제공하고, 제출된 answer를 채점하며,
    시간 예산과 trace를 관리하는 평가 환경.
    """

    def __init__(
        self,
        task_list: Optional[list] = None,
        time_budget_sec: Optional[float] = None,
        enable_trace: bool = True,
        max_attempts_per_pair: int = DEFAULT_MAX_ATTEMPTS_PER_PAIR,
    ):
        """
        Args:
            task_list: 수행할 task 식별자 목록.
                - None: ARCManager 매핑 순서대로 전체 벤치마크.
                - list[int]: task 인덱스 목록.
                - list[str]: task hex 코드 목록 (예: ["easy0001", "easy0004"]).
            time_budget_sec: 에피소드 전체 시간 제한(초). None이면 무제한.
            enable_trace: step마다 trace 기록 여부.
            max_attempts_per_pair: test pair당 최대 제출 횟수. 3이면 3번 틀리면 해당 task 실패.
        """
        self._time_budget_sec = time_budget_sec
        self._enable_trace = enable_trace
        self._max_attempts_per_pair = max_attempts_per_pair
        self._trace: list[dict] = []
        self._episode_start_time: Optional[float] = None

        # task 순서 결정
        if task_list is None:
            index_to_json, _ = ARCManager._build_task_mapping()
            self._task_ids = [index_to_json[i] for i in sorted(index_to_json)]
        elif task_list and isinstance(task_list[0], int):
            index_to_json, _ = ARCManager._build_task_mapping()
            self._task_ids = [index_to_json[i] for i in task_list if i in index_to_json]
        else:
            self._task_ids = list(task_list) if task_list else []

        self._current_index: int = -1
        self._current_task: Optional[TASK] = None
        self._current_task_json: Optional[dict] = None
        self._done: bool = True
        self._episode_task_ids: list = []
        # test pair당 남은 제출 횟수. 새 task 로드 시 초기화.
        self._attempts_left: list[int] = []

    def reset(self, task_list: Optional[list] = None) -> Optional[dict]:
        """
        새 에피소드 시작.

        Args:
            task_list: 이번 에피소드에만 사용할 task 목록. None이면 생성자에서 준 목록 사용.

        Returns:
            첫 번째 task의 JSON (task가 있으면), 없으면 None.
        """
        self._episode_task_ids = list(task_list) if task_list is not None else list(self._task_ids)
        self._current_index = -1
        self._current_task = None
        self._current_task_json = None
        self._trace = []
        self._done = not self._episode_task_ids
        self._episode_start_time = time.perf_counter()

        if self._done:
            return None
        return self._advance_to_next_task()

    def _advance_to_next_task(self) -> Optional[dict]:
        """다음 task로 이동하고 해당 task JSON 반환."""
        if self._time_budget_sec is not None and self._episode_start_time is not None:
            if time.perf_counter() - self._episode_start_time >= self._time_budget_sec:
                self._done = True
                return None

        self._current_index += 1
        if self._current_index >= len(self._episode_task_ids):
            self._done = True
            return None

        task_id = self._episode_task_ids[self._current_index]
        try:
            self._current_task = ARCManager.from_hex_code(task_id)
            self._current_task_json = self._task_to_agent_json(self._current_task)
            n = len(self._current_task.test_pairs)
            self._attempts_left = [self._max_attempts_per_pair] * n
            return self._current_task_json
        except FileNotFoundError:
            return self._advance_to_next_task()

    def _task_to_agent_json(self, task: TASK) -> dict:
        """에이전트에게 줄 task 표현 (raw_data 기반, task_id 포함)."""
        out = dict(task.raw_data)
        out["task_id"] = task.hex_code
        return out

    def get_task(self) -> Optional[dict]:
        """
        현재 task JSON 반환.
        Returns:
            {"task_id": str, "train": [...], "test": [...]} 또는 None (에피소드 종료 후).
        """
        if self._current_task_json is None:
            return None
        return self._current_task_json

    def get_current_task_id(self) -> Optional[str]:
        """현재 task의 hex 코드. 없으면 None."""
        if self._current_task is None:
            return None
        return self._current_task.hex_code

    def step(self, answer: Any) -> tuple[float, Optional[dict], bool, dict]:
        """
        에이전트의 answer를 채점. test pair당 최대 max_attempts_per_pair회 제출 가능.
        틀리면 같은 task로 재제출 가능(can_retry). 3번 다 틀리면 해당 task 실패 후 다음 task로.

        Args:
            answer: 제출 답. test pair 순서와 동일한 길이의 출력 그리드 목록.
                각 원소는 list[list[int]] (view 형식).
                test pair가 1개면 단일 그리드(list[list[int]])도 허용.

        Returns:
            (reward, next_task, done, info)
            - reward: 1.0 = 전부 맞음, 0.0 = 틀림 또는 일부만 맞음.
            - next_task: 다음에 풀 task JSON. can_retry면 현재 task(같은 것) 반환.
            - done: 에피소드 종료 여부.
            - info: {"attempts_left": [int,...], "correct_per_pair": [bool,...], "can_retry": bool}
        """
        reward = 0.0
        info = {"attempts_left": [], "correct_per_pair": [], "can_retry": False}
        if self._current_task is None:
            return reward, None, True, info

        # answer를 리스트로 정규화: [grid0, grid1, ...], 단일 그리드면 [grid]
        if not isinstance(answer, list):
            answer = [answer]
        if answer and isinstance(answer[0], (list, tuple)):
            if answer[0] and isinstance(answer[0][0], (list, tuple)):
                pass
            else:
                answer = [answer]

        test_pairs = self._current_task.test_pairs
        n = len(test_pairs)
        if len(self._attempts_left) != n:
            self._attempts_left = [self._max_attempts_per_pair] * n

        correct_per_pair = []
        if len(answer) != n:
            reward = 0.0
            correct_per_pair = [False] * n
        else:
            for i, test_pair in enumerate(test_pairs):
                if getattr(self._current_task, "test_output_ground_truth", None) and i < len(self._current_task.test_output_ground_truth):
                    gt_view = self._current_task.test_output_ground_truth[i]
                else:
                    gt_view = test_pair.output_grid.view if hasattr(test_pair.output_grid, "view") else test_pair.output_grid
                ok = _grids_equal(answer[i], gt_view)
                correct_per_pair.append(ok)
                if not ok:
                    self._attempts_left[i] -= 1
            all_correct = all(correct_per_pair)
            reward = 1.0 if all_correct else 0.0

        info["correct_per_pair"] = correct_per_pair
        info["attempts_left"] = list(self._attempts_left)

        # trace 기록
        if self._enable_trace:
            self._trace.append({
                "task_id": self.get_current_task_id(),
                "reward": reward,
                "correct_per_pair": correct_per_pair,
                "attempts_left": list(self._attempts_left),
                "answer_len": len(answer) if isinstance(answer, list) else 0,
                "elapsed_sec": time.perf_counter() - self._episode_start_time if self._episode_start_time else None,
            })

        # 시간 예산 체크
        if self._time_budget_sec is not None and self._episode_start_time is not None:
            if time.perf_counter() - self._episode_start_time >= self._time_budget_sec:
                next_task = None
                done = True
                return reward, next_task, done, info

        if reward >= 1.0:
            next_task = self._advance_to_next_task()
            done = self._done
            return reward, next_task, done, info

        # 틀린 경우: 어떤 pair라도 시도 횟수 소진이면 이 task 실패 → 다음 task로
        any_failed = any(
            self._attempts_left[i] <= 0 and not correct_per_pair[i]
            for i in range(n)
        )
        if any_failed:
            next_task = self._advance_to_next_task()
            done = self._done
            return reward, next_task, done, info

        # 아직 재시도 가능
        info["can_retry"] = True
        next_task = self.get_task()  # 같은 task 유지
        return reward, next_task, False, info

    def run_single_task(self, task_id: str, agent: Optional[Any] = None) -> tuple[float, dict]:
        """
        특정 문제 하나만 테스트.

        Args:
            task_id: task hex 코드 (예: "easy0004").
            agent: 있으면 agent.solve(task) 호출 후 채점하여 반환. 없으면 task만 로드해 info만 반환.

        Returns:
            (reward, info): reward 1.0/0.0, info에는 task_id, correct, (선택) trace 등.
        """
        self.reset(task_list=[task_id])
        task_json = self.get_task()
        if task_json is None:
            return 0.0, {"task_id": task_id, "error": "task not found", "correct": False}

        if agent is None:
            return 0.0, {
                "task_id": task_id,
                "task_json": task_json,
                "num_test_pairs": len(self._current_task.test_pairs) if self._current_task else 0,
            }

        # test pair당 최대 3회 제출. 틀리면 can_retry 시 같은 task로 다시 solve → step
        num_submissions = 0
        step_info = None
        while True:
            answer = agent.solve(task_json, step_info=step_info) if _solve_accepts_step_info(agent) else agent.solve(task_json)
            reward, next_task, done, info = self.step(answer)
            num_submissions += 1
            step_info = {**(info or {}), "submission_index": num_submissions}
            if reward >= 1.0:
                break
            if not info.get("can_retry"):
                break
            task_json = self.get_task()
            if task_json is None:
                break
        return reward, {
            "task_id": task_id,
            "correct": reward >= 1.0,
            "reward": reward,
            "num_submissions": num_submissions,
            "attempts_left": info.get("attempts_left", []),
            "trace": self.get_trace(),
        }

    def run_benchmark(
        self,
        agent: Any,
        n: Optional[int] = None,
    ) -> dict:
        """
        에이전트로 벤치마크 실행: reset → (get_task → agent.solve → step → agent.update_memory) 반복.

        Args:
            agent: .solve(task_json) -> answer, .update_memory(reward) 호출 가능한 객체.
            n: 최대 수행 task 수. None이면 전부.

        Returns:
            {"correct": int, "total": int, "results": list, "trace": list}
        """
        episode_list = self._task_ids[:n] if n is not None else self._task_ids
        if not episode_list:
            return {"correct": 0, "total": 0, "results": [], "trace": []}

        self.reset(task_list=episode_list)
        results = []
        correct = 0

        while not self._done:
            task = self.get_task()
            if task is None:
                break
            task_id = self.get_current_task_id()
            # task당 최대 3회 제출 가능. can_retry면 같은 task로 재시도
            step_info = None
            num_submissions = 0
            while True:
                answer = agent.solve(task, step_info=step_info) if _solve_accepts_step_info(agent) else agent.solve(task)
                reward, next_task, done, info = self.step(answer)
                num_submissions += 1
                step_info = {**(info or {}), "submission_index": num_submissions}
                if reward >= 1.0:
                    correct += 1
                if hasattr(agent, "update_memory"):
                    agent.update_memory(reward)
                if reward >= 1.0 or not info.get("can_retry"):
                    break
                task = self.get_task()
                if task is None:
                    break
            results.append({
                "task_id": task_id,
                "reward": reward,
                "num_submissions": num_submissions,
                "attempts_left": info.get("attempts_left", []),
            })

        return {
            "correct": correct,
            "total": len(results),
            "results": results,
            "trace": list(self._trace),
        }

    def get_trace(self) -> list[dict]:
        """현재 에피소드의 trace 목록 반환."""
        return list(self._trace)

    def save_trace(self, path: str | Path) -> None:
        """trace를 JSON 파일로 저장."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._trace, f, indent=2, ensure_ascii=False)
