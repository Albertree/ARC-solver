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
    print("[*] 태스크 로드...")
    try:
        from basics.viz import show_task
        from managers.arc_manager import ARCManager

        manager = ARCManager(data_root="data", semantic_memory_root="semantic_memory")
        task = manager.load_task(TASK_HEX)
        print(f"    Task: {task}")
        show_task(task)

    except Exception:
        print("[!] 태스크 로드 실패:")
        traceback.print_exc()
        sys.exit(1)

    # 2. WM + SOAR cycle with trace logging
    print("\n[*] WM + SOAR cycle (Elaborate → Propose → Select → Apply)...")
    try:
        from agent.wm import WorkingMemory
        from agent.wm_logger import reset_wm_snapshot
        from agent.io import inject_arc_task
        from agent.agent_common import build_wm_from_task
        from agent.elaboration_rules import build_elaborator
        from agent.rules import build_proposer
        from agent.cycle import run_cycle
        from agent.trace_logger import TraceLogger

        wm = WorkingMemory()
        reset_wm_snapshot(wm)

        # 환경 input function: task를 input-link로 주입
        inject_arc_task(task, wm)

        # goal / focus / subgoals 설정
        wm.s1["goal"] = {}
        build_wm_from_task(task, wm)

        # LTM에서 기존 rule 로드 (E-01 retrieval 지원)
        from agent.memory import load_rules_from_ltm
        existing_rules = load_rules_from_ltm(TASK_HEX, "semantic_memory")
        if existing_rules:
            wm.s1["active_rules"] = existing_rules
            print(f"    Loaded {len(existing_rules)} existing rules from procedural_memory")

        elaborator = build_elaborator()
        proposer = build_proposer()

        # Trace logger 시작
        trace_logger = TraceLogger(TASK_HEX)
        trace_logger.start()

        out = run_cycle(
            wm,
            elaborator,
            proposer,
            max_steps=200,
            stop_on_goal=True,
            log_wm=True,
            trace_logger=trace_logger,
        )

        # [결과] 블록 출력
        goal = wm.s1.get("goal", {})
        subgoals = goal.get("subgoals", {})
        found = wm.s1.get("found", {})
        success = all(
            sg.get("status") == "solved"
            for sg in subgoals.values()
            if isinstance(sg, dict)
        )
        # 적용된 rule 정보
        applied_rules = []
        for k, f in found.items():
            if isinstance(f, dict):
                applied_rules.append(
                    f"{f.get('rule_id', '?')} (retrieval_score: {f.get('retrieval_score', '?')})"
                )
        rule_info = ", ".join(applied_rules) if applied_rules else "없음"
        output_info = "semantic_memory에 저장된 predicted 결과" if success else "없음"
        trace_logger.write_result(success, rule_info, output_info)

        trace_logger.stop()

        # Episodic memory 저장
        from agent.memory import save_episode
        episode_path = save_episode(TASK_HEX, wm, success)
        print(f"\n[cycle] {out}")
        print(f"[log] Trace log saved to: {trace_logger.log_path}")
        print(f"[episodic] Episode saved to: {episode_path}")

    except Exception:
        print("[!] WM / cycle ��패:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
