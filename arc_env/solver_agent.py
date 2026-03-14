"""
SolverAgent: solver_main 흐름을 ARCEnvironment용 에이전트로 감싼 구현.
- solve(task_json) → test 출력 그리드 목록 (env.step 형식)
- update_memory(reward) → 선택적 메모리 갱신
"""

import os
from typing import Any, List, Optional

# 에이전트 모드: printcg 대기/input 비활성화
ENV_AGENT_MODE = "ARC_AGENT_MODE"

from managers.arc_manager import ARCManager
from workers.arc_solver import ARCSolver
from program_gen import save_abstract_program
from program_gen.manager import ProgramManager
from basics.utils import printcg, print_grids_side_by_side


# 기본 추상 프로그램/실행 디렉터리 (solver_main과 동일)
DEFAULT_BASE_OUTPUT_DIR = "outputs/generated_codes"


def _grid_to_view(grid: Any) -> List[List[int]]:
    """GRID 또는 view 형태를 list[list[int]]로 반환."""
    if grid is None:
        return []
    if hasattr(grid, "view"):
        return grid.view
    if isinstance(grid, list) and grid and isinstance(grid[0], (list, tuple)):
        return [list(row) for row in grid]
    return []


def _placeholder_grid(rows: int, cols: int, fill: int = 0) -> List[List[int]]:
    """채점 실패 시 제출할 기본 그리드 (같은 크기, fill 색)."""
    if rows <= 0 or cols <= 0:
        return [[fill]]
    return [[fill] * cols for _ in range(rows)]


def grid_repr(grid: List[List[int]], max_rows: int = 6, max_cols: int = 12) -> str:
    """로그용 그리드 요약 문자열 (작으면 전부, 크면 잘라서)."""
    if not grid or not grid[0]:
        return "[]"
    rows = grid[:max_rows]
    lines = []
    for r in rows:
        part = r[:max_cols]
        line = " ".join(str(c) for c in part)
        if len(r) > max_cols:
            line += " ..."
        lines.append(line)
    if len(grid) > max_rows:
        lines.append("...")
    return "\n  ".join(lines)


class SolverAgent:
    """
    solver_main과 동일한 파이프라인을 사용하는 에이전트.
    - 목적 세우기 → test() (PaG1 예측 또는 pair program 생성) → 필요 시 추상 프로그램 실행.
    """

    def __init__(
        self,
        base_output_dir: str = DEFAULT_BASE_OUTPUT_DIR,
        verbose: bool = False,
        on_step: Any = None,
    ):
        """
        Args:
            base_output_dir: 추상 프로그램 저장 경로.
            verbose: True면 solve() 중 단계별 로그와 중간/최종 그리드 요약을 stdout에 출력.
            on_step: (step_name: str, data: dict) -> None 콜백. 각 단계마다 호출되며,
                data에 task_id, grid, level, test_idx 등이 포함될 수 있음.
        """
        self.base_output_dir = base_output_dir
        self._pm = ProgramManager(base_output_dir=base_output_dir)
        self.verbose = verbose
        self.on_step = on_step  # callable(step_name: str, data: dict) or None

    def _phase(self, phase: str, msg: str) -> None:
        """단계별 디버깅용 한 줄 라인. 항상 출력.
        흐름: [Agent] start → memory load → working memory init → task received
              → [Task] visualize (printcg) → [Agent] goal set
              → [Solver] test() start → [Solver] PAIR 간 GRID 비교 → [Solver] PaG1 예측 시도
              → [Solver] PaG1 성공/불가 → [Solver] PAIR N GRID/OBJECT/PIXEL level
              → [Agent] PaG1 사용 or 추상 저장·실행 → [Agent] 제출 Input|Output|GT → [Agent] done
        """
        print(f"  [{phase}] {msg}")

    def _log(self, step: str, data: dict, print_grid: bool = False) -> None:
        if self.verbose:
            msg = f"  [SolverAgent] {step}"
            for k, v in data.items():
                if k != "grid":
                    msg += f"  {k}={v}"
            print(msg)
            if print_grid and data.get("grid") is not None:
                printcg(data["grid"])
        if callable(self.on_step):
            self.on_step(step, data)

    def solve(self, task: dict, step_info: Optional[dict] = None) -> Any:
        """
        env.get_task()에서 받은 task JSON으로 한 번 풀고, test 출력 그리드 목록 반환.

        Args:
            task: env.get_task() 반환값.
            step_info: 재시도 시 이전 step()의 info. correct_per_pair, attempts_left 등으로
                다른 전략(예: OBJECT/PIXEL) 시도에 활용 가능.

        Returns:
            list[list[list[int]]]: test pair 순서대로 각 출력 그리드 (view 형식).
        """
        task_id = task.get("task_id")
        if not task_id:
            return []

        self._phase("Agent", "start")
        self._phase("Agent", "long-term memory load (task JSON from env)")
        self._phase("Agent", "working memory init")
        self._phase("Agent", f"task received task_id={task_id}")

        prev_agent_mode = os.environ.pop(ENV_AGENT_MODE, None)
        os.environ[ENV_AGENT_MODE] = "1"
        try:
            solver = ARCSolver(task_id, interactive=False)
        except FileNotFoundError:
            if prev_agent_mode is not None:
                os.environ[ENV_AGENT_MODE] = prev_agent_mode
            else:
                os.environ.pop(ENV_AGENT_MODE, None)
            return []

        try:
            self._phase("Task", "visualize (train + test pairs)")
            if self.verbose:
                printcg(solver.task.view)
            solver._set_goal_from_task_and_pairs()
            self._phase("Agent", f"goal set: {getattr(solver, 'goal', 'N/A')}")
            self._phase("Solver", "test() start — PAIR 비교·PaG1·pair program")
            solver.test()

            task_obj = solver.task
            test_pairs = task_obj.test_pairs
            if not test_pairs:
                return []

            # 1) PaG1 예측: test pair별로 독립. 후보가 있으면 submission_index로 선택, 소진된 pair만 추상으로
            n_pairs = len(test_pairs)
            answers = [None] * n_pairs
            submission_index = (step_info or {}).get("submission_index", 0)
            predictions = getattr(solver, "_test_output_predictions", None)
            candidates_list = getattr(solver, "_test_output_prediction_candidates_list", None)

            if predictions is not None and len(predictions) == n_pairs:
                for i in range(n_pairs):
                    cands = candidates_list[i] if candidates_list and i < len(candidates_list) else None
                    if cands is None and predictions[i] is not None:
                        cands = [predictions[i]]
                    if cands and submission_index < len(cands):
                        v = _grid_to_view(cands[submission_index])
                        if v:
                            answers[i] = v
                            self._phase("Agent", f"PaG1 pair {i} 후보 {submission_index + 1}/{len(cands)} 제출")
            else:
                # 단일 pair 호환 (리스트 미사용 시)
                single_candidates = getattr(solver, "_test_output_prediction_candidates", None)
                if single_candidates is None and getattr(solver, "_test_output_prediction", None) is not None:
                    single_candidates = [solver._test_output_prediction]
                if single_candidates and n_pairs == 1 and submission_index < len(single_candidates):
                    v = _grid_to_view(single_candidates[submission_index])
                    if v:
                        answers[0] = v
                        self._phase("Agent", f"PaG1 후보 {submission_index + 1}/{len(single_candidates)} 제출")

            # 2) 비어 있는 pair는 추상 프로그램으로 채움
            need_abstract = any(a is None for a in answers)
            if need_abstract:
                self._phase("Agent", "PaG1 없음/후보 소진인 pair → 추상 프로그램 경로")
                for level in ("GRID", "OBJECT", "PIXEL"):
                    self._phase("Agent", f"추상 프로그램 저장 {level}")
                    path = save_abstract_program(
                        task_id,
                        level=level,
                        base_output_dir=self.base_output_dir,
                    )
                    self._log("save_abstract", {"task_id": task_id, "level": level, "path": path})

                level_order = ("GRID", "OBJECT", "PIXEL") if step_info else ("PIXEL", "OBJECT", "GRID")
                level_order_str = "→".join(level_order)

                for test_idx, test_pair in enumerate(test_pairs):
                    if answers[test_idx] is not None:
                        continue
                    self._phase("Agent", f"추상 실행 test_pair {test_idx} ({level_order_str} 시도)")
                    test_input_grid = test_pair.input_grid
                    t_view = _grid_to_view(test_input_grid)
                    rows = len(t_view) if t_view else 1
                    cols = len(t_view[0]) if t_view and t_view[0] else 1

                    out_grid = None
                    used_level = None
                    for level in level_order:
                        abstract_path = os.path.join(
                            self.base_output_dir,
                            task_id,
                            level,
                            f"{task_id}_abstract_{level.lower()}.py",
                        )
                        if not os.path.isfile(abstract_path):
                            continue
                        try:
                            result = self._pm.execute_program(abstract_path, test_input_grid)
                            if result is not None:
                                out_grid = result
                                used_level = level
                                break
                        except Exception as e:
                            if self.verbose:
                                print(f"  [SolverAgent] abstract run failed  task_id={task_id} level={level} test_idx={test_idx} err={e}")
                            continue

                    if out_grid is not None:
                        view = _grid_to_view(out_grid)
                        answers[test_idx] = view
                        self._log(
                            "abstract_result",
                            {"task_id": task_id, "test_idx": test_idx, "level": used_level, "grid": view},
                            print_grid=True,
                        )
                    else:
                        answers[test_idx] = _placeholder_grid(rows, cols, fill=0)
                        self._log(
                            "placeholder",
                            {"task_id": task_id, "test_idx": test_idx, "shape": (rows, cols)},
                        )

            # 최종적으로 None이 남으면 placeholder (방어)
            for i in range(n_pairs):
                if answers[i] is None:
                    t_view = _grid_to_view(test_pairs[i].input_grid)
                    r = len(t_view) if t_view else 1
                    c = len(t_view[0]) if t_view and t_view[0] else 1
                    answers[i] = _placeholder_grid(r, c, fill=0)

            # 제출 전 항상 Input | Output | GT 표시 (GT는 task.test_output_ground_truth 사용)
            if answers and test_pairs:
                self._phase("Agent", "제출: Input | Output | GT (맞음/틀림 확인)")
                for idx, (test_pair, ans_view) in enumerate(zip(test_pairs, answers)):
                    inp = test_pair.input_grid
                    if getattr(task_obj, "test_output_ground_truth", None) and idx < len(task_obj.test_output_ground_truth):
                        gt = task_obj.test_output_ground_truth[idx]
                    else:
                        gt = test_pair.output_grid
                    print(f"\n  [Agent] Test pair {idx}: Input  |  Output  |  GT")
                    print_grids_side_by_side(
                        ["Input", "Output", "GT"],
                        [inp, ans_view, gt],
                    )

            self._phase("Agent", f"done  num_answers={len(answers)}")
            self._log("done", {"task_id": task_id, "num_answers": len(answers)})
            return answers
        finally:
            if prev_agent_mode is not None:
                os.environ[ENV_AGENT_MODE] = prev_agent_mode
            else:
                os.environ.pop(ENV_AGENT_MODE, None)

    def update_memory(self, reward: float) -> None:
        """
        채점 결과로 메모리(로컬 JSON 등) 갱신.
        현재는 no-op. 추후 kg_rules.json 등 연동 시 구현.
        """
        pass
