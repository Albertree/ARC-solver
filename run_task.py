"""
단일 태스크 실행 스크립트 — 에러 추적용.
python run_task.py
"""

import json
import sys
import traceback


TASK_HEX = "easy0014"


def main():
    print(f"=== run_task: {TASK_HEX} ===\n")

    # 1. 태스크 로드
    print("[*] 태스크 로드...")
    try:
        from basics.viz import show_task, _print_side_by_side
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
        output_info = "predicted output grid 생성됨" if success else "없음"
        trace_logger.write_result(success, rule_info, output_info)

        trace_logger.stop()

        # Episodic memory 저장
        from agent.memory import save_episode
        episode_path = save_episode(TASK_HEX, wm, success)
        print(f"\n[cycle] {out}")
        print(f"[log] Trace log saved to: {trace_logger.log_path}")
        print(f"[episodic] Episode saved to: {episode_path}")

        # 3. 결과 검증: predicted output vs expected output
        print("\n" + "=" * 50)
        print("결과 검증")
        print("=" * 50)
        _verify_results(task, found, _print_side_by_side)

    except Exception:
        print("[!] WM / cycle 실패:")
        traceback.print_exc()
        sys.exit(1)


def _verify_results(task, found, print_side_by_side_fn):
    """predicted output과 expected output을 비교하여 결과를 출력한다."""
    for i, test_pair in enumerate(task.test_pairs):
        test_key = f"test_{i}"
        test_found = found.get(test_key, {})
        predicted = test_found.get("predicted_output") if isinstance(test_found, dict) else None

        print(f"\n[Test {i}] {test_pair.node_id}")

        if predicted is None:
            print("  predicted output: 없음 (규칙 적용 실패)")
            continue

        # expected output 로드
        import os
        expected = None
        candidates = [
            f"data/ARC_AGI/training/{task.task_hex}.json",
            f"data/ARC_AGI/evaluation/{task.task_hex}.json",
            f"data/ARC_easy/{task.task_hex}.json",
            f"data/{task.task_hex}.json",
        ]
        for data_path in candidates:
            if os.path.exists(data_path):
                try:
                    with open(data_path) as f:
                        raw = json.load(f)
                    if i < len(raw["test"]):
                        expected = raw["test"][i].get("output")
                    break
                except Exception:
                    pass

        # 시각화: test input | predicted | expected
        print("  [Test Input]    [Predicted]    [Expected]")
        grids = [test_pair.input_grid.raw]
        grids.append(predicted)
        if expected:
            grids.append(expected)
        print_side_by_side_fn(grids, gap=4)

        # 정확도 검사
        if expected:
            correct = predicted == expected
            if correct:
                print(f"\n  *** CORRECT *** 예측이 정답과 일치합니다!")
            else:
                # 셀 단위 비교
                total = sum(len(row) for row in expected)
                diff_count = 0
                for r in range(len(expected)):
                    for c in range(len(expected[0])):
                        pred_val = predicted[r][c] if r < len(predicted) and c < len(predicted[0]) else -1
                        if pred_val != expected[r][c]:
                            diff_count += 1
                accuracy = (total - diff_count) / total * 100
                print(f"\n  INCORRECT: {diff_count}/{total} 셀 불일치 (정확도: {accuracy:.1f}%)")
        else:
            print("\n  (expected output 없음 — 비교 불가)")


if __name__ == "__main__":
    main()
