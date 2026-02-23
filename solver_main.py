import os
from managers.arc_manager import ARCManager
from workers.arc_solver import ARCSolver
from basics.utils import printcg, print_grids_side_by_side
from program_gen import save_abstract_program
from program_gen.manager import ProgramManager


def _wait_enter(msg: str = "다음 단계로 진행하려면 Enter를 누르세요..."):
    input(f"[solver_main] {msg}")


if __name__ == "__main__":

    # TASK_HEX_CODE = "08ed6ac7"
    # TASK_HEX_CODE = "007bbfb7"
    # TASK_HEX_CODE = "a61f2674" # 가장 길고 짧은 회색 막대 파랑 빨강으로 칠하고 나머지 회색막대 지우기
    # TASK_HEX_CODE = "aabf363d" # 객체 좌하단 픽셀 색으로 색칠하기
    # TASK_HEX_CODE = "ae3edfdc" # 빨강 파랑 점 기준으로 픽셀 모임
    # TASK_HEX_CODE = "00000000" # 내가 만든 rotate 문제
    # TASK_HEX_CODE = "1b8318e3" # 회색 객체로 모이는 픽셀 이동
    # TASK_HEX_CODE = "b745798f" # 테두리 구석 칠하기
    TASK_HEX_CODE = "easy0004" # easy0001

    print(f"\n[solver_main] ========== 1) TASK 로드 및 목적 세우기 ==========")
    print(f"[solver_main] TASK 로드: {TASK_HEX_CODE}")
    task = ARCManager.from_hex_code(TASK_HEX_CODE)
    print(f"[solver_main] example_pairs={len(task.example_pairs)}, test_pairs={len(task.test_pairs)}")

    solver = ARCSolver(TASK_HEX_CODE)
    solver._set_goal_from_task_and_pairs()
    # printcg가 화면을 지우므로, 먼저 그리드만 띄운 뒤 요약을 그 아래에 출력
    printcg(task.view, wait_for_enter=False)
    print(f"\n[solver_main] ---------- 1) 요약 ----------")
    print(f"[solver_main] goal = {getattr(solver, 'goal', 'N/A')}")
    print(f"[solver_main] 목적 = {getattr(solver, '_goal_reason', 'N/A')}")
    if getattr(task, "property", None):
        print(f"[solver_main] TASK property = {task.property}")
    print(f"[solver_main] ----------------------------------------")
    _wait_enter("1) 완료. 다음 단계(Solver)로 진행하려면 Enter를 누르세요...")

    print(f"\n[solver_main] ========== 2) Solver: pair program 생성 (test) ==========")
    solver.test()

    # 예측으로 종료된 경우: 예측 output vs GT만 보여주고, 추상화·실행 for 루프는 아예 스킵
    if getattr(solver, "_finished_by_pa_g1_prediction", False):
        print(f"\n[solver_main] (예측으로 종료) 예측 output vs GT 비교")
        if task.test_pairs and getattr(solver, "_test_output_prediction", None) is not None:
            test_pair = task.test_pairs[0]
            t_view = test_pair.input_grid.view if hasattr(test_pair.input_grid, "view") else test_pair.input_grid
            gt_view = test_pair.output_grid.view if hasattr(test_pair.output_grid, "view") else test_pair.output_grid
            pred_view = solver._test_output_prediction
            print_grids_side_by_side(["Test input", "예측 output", "GT output"], [t_view, pred_view, gt_view])
        _wait_enter("종료하려면 Enter를 누르세요...")
        print("[solver_main] === 종료 ===")
    else:
        print(f"[solver_main] 2) 완료. goal={getattr(solver, 'goal', 'N/A')}")
        _wait_enter("2) 완료. 다음 단계(추상화)로 진행하려면 Enter를 누르세요...")

        print(f"\n[solver_main] ========== 3) 추상화: pair program → abstract program ==========")
        for level in ("GRID", "OBJECT", "PIXEL"):
            path = save_abstract_program(TASK_HEX_CODE, level=level)
            if path:
                print(f"[solver_main]   {level}: 저장됨 → {path}")
            else:
                print(f"[solver_main]   {level}: pair program 없음 (추상화 스킵)")
        _wait_enter("3) 완료. 다음 단계(추상 프로그램 실행)로 진행하려면 Enter를 누르세요...")

        print(f"\n[solver_main] ========== 4) 추상 프로그램으로 test input 실행 ==========")
        printcg(task.view, wait_for_enter=False)
        base_dir = "outputs/generated_codes"
        pm = ProgramManager(base_output_dir=base_dir)
        if not task.test_pairs:
            print("[solver_main] test pair 없음 → 추상 프로그램 실행 스킵")
        else:
            test_pair = task.test_pairs[0]
            test_input_grid = test_pair.input_grid
            gt_output_grid = test_pair.output_grid
            for level in ("GRID", "OBJECT", "PIXEL"):
                abstract_path = os.path.join(base_dir, TASK_HEX_CODE, level, f"{TASK_HEX_CODE}_abstract_{level.lower()}.py")
                if not os.path.isfile(abstract_path):
                    continue
                print(f"[solver_main] LEVEL: {level} (abstract program 실행)")
                # Build three grids for one row: test input | output | gt output
                t_view = test_input_grid.view if hasattr(test_input_grid, "view") else test_input_grid
                gt_view = gt_output_grid.view if hasattr(gt_output_grid, "view") else gt_output_grid
                result = pm.execute_program(abstract_path, test_input_grid)
                if result is not None:
                    out_view = result.view if hasattr(result, "view") else result
                else:
                    # Placeholder same shape as test input (14 = dark gray)
                    if t_view and t_view[0]:
                        rows, cols = len(t_view), len(t_view[0])
                        out_view = [[14] * cols for _ in range(rows)]
                    else:
                        out_view = []
                labels = ["Test input", "Output (없음)" if result is None else "Output", "GT output"]
                print_grids_side_by_side(labels, [t_view, out_view, gt_view])
                print()
        _wait_enter("종료하려면 Enter를 누르세요...")
        print("[solver_main] === 종료 ===")
    # solver.object_mapping()
    