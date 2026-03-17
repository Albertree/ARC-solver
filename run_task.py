"""
단일 태스크 실행 스크립트 — 에러 추적용.
python run_task.py
"""

import sys
import traceback

TASK_HEX = "08ed6ac7"


def main():
    print(f"=== run_task: {TASK_HEX} ===\n")

    # 1. 태스크 로드
    print("[1] 태스크 로드...")
    try:
        from managers.arc_manager import ARCManager
        manager = ARCManager(data_root="data", semantic_memory_root="semantic_memory")
        task = manager.load_task(TASK_HEX)
        print(f"    Task: {task}")
        print(f"    example_pairs: {len(task.example_pairs)}")
        print(f"    test_pairs:    {len(task.test_pairs)}")
    except Exception:
        print("[!] 태스크 로드 실패:")
        traceback.print_exc()
        sys.exit(1)

    # 2. WM 초기화
    print("\n[2] WorkingMemory 초기화...")
    try:
        from agent.wm import WorkingMemory
        from agent.agent_common import build_wm_from_task
        wm = WorkingMemory()
        build_wm_from_task(task, wm)
        print(f"    goal:     {wm.get('goal')}")
        print(f"    subgoals: {wm.get('subgoals')}")
    except Exception:
        print("[!] WM 초기화 실패:")
        traceback.print_exc()
        sys.exit(1)

    # 3. Elaborator / Proposer 생성
    print("\n[3] Elaborator / Proposer 생성...")
    try:
        from agent.elaboration_rules import build_elaborator
        from agent.rules import build_proposer
        elaborator = build_elaborator()
        proposer = build_proposer()
        print(f"    elaborator: {elaborator}")
        print(f"    proposer:   {proposer}")
    except Exception:
        print("[!] Elaborator/Proposer 생성 실패:")
        traceback.print_exc()
        sys.exit(1)

    # 4. 사이클 실행
    print("\n[4] run_cycle (max_steps=50)...")
    try:
        from agent.cycle import run_cycle
        run_cycle(wm, elaborator, proposer, max_steps=50)
        print("    사이클 완료")
    except Exception:
        print("[!] 사이클 실패:")
        traceback.print_exc()
        sys.exit(1)

    # 5. 결과 추출
    print("\n[5] 결과 추출...")
    try:
        from agent.agent_common import answers_from_wm
        answers = answers_from_wm(wm)
        if answers is None:
            print("    answers: None (answers_from_wm 미구현)")
        else:
            print(f"    answers: {len(answers)} grids")
            for i, g in enumerate(answers):
                if g is None:
                    print(f"      test_{i}: None")
                else:
                    print(f"      test_{i}: {len(g)}x{len(g[0]) if g else 0}")
    except Exception:
        print("[!] 결과 추출 실패:")
        traceback.print_exc()
        sys.exit(1)

    print("\n=== 완료 ===")


if __name__ == "__main__":
    main()
