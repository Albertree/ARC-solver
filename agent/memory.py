"""
memory — SOAR Chunking 및 LTM 저장.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] Chunking은 subgoal이 해결된 시점에 트리거된다.
            reasoning trace → production rule로 압축된다.

[설계 자유] 압축된 production rule의 형태.
            LTM에 저장하는 형식 (ARCKG edge JSON 등).
            load 타이밍과 방식.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import os
import glob
from datetime import datetime


def chunk_from_substate(substate: dict) -> dict:
    """
    [SOAR 강제] subgoal 해결 시 chunking이 트리거된다.
    [설계 자유] 압축 결과(rule dict)의 형태.
    MUST NOT: 실패한 substate를 chunk하지 마.
    """
    raise NotImplementedError("chunk_from_substate() not implemented.")


def save_rule_to_ltm(rule: dict, task_hex: str,
                     semantic_memory_root: str) -> str:
    """
    [설계 자유] LTM에 rule을 어떤 형식으로 저장할지.
    MUST NOT: 기존 rule 파일을 덮어쓰지 마 — n 증가로 새 파일 생성.
    """
    raise NotImplementedError("save_rule_to_ltm() not implemented.")


def load_rules_from_ltm(task_hex: str, semantic_memory_root: str) -> list:
    """
    [설계 자유] LTM에서 rule을 읽어 active_rules 형식으로 반환.
    MUST NOT: solve 루프 내부에서 호출하지 마 — solve() 시작 전 1회만.
    """
    rules = []
    pattern = "procedural_memory/R_*.json"
    for path in sorted(glob.glob(pattern)):
        try:
            with open(path, "r") as f:
                rule = json.load(f)
            rules.append({
                "ref": path,
                "confidence": rule.get("confidence", 0),
                "rule": rule,
            })
        except Exception:
            continue
    return rules


# ---------------------------------------------------------------------------
# Episodic Memory
# ---------------------------------------------------------------------------

def save_episode(task_hex: str, wm, success: bool,
                 episodic_memory_root: str = "episodic_memory") -> str:
    """
    태스크 풀이 에피소드를 episodic_memory에 JSON으로 저장한다.

    에피소드 내용:
    - task_hex: 태스크 ID
    - timestamp: 생성 시각
    - success: 성공 여부
    - rule_attempts: 시도한 rule 목록 (순서대로, 성공/실패/실패 이유 포함)
    - matching_results: Object Matching 결과 요약
    - invariants: 추출된 invariant 목록
    - transform_targets: 추출된 transformation target 목록
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # rule attempts 구성
    found = wm.s1.get("found", {})
    active_rules = wm.s1.get("active_rules", [])
    goal = wm.s1.get("goal", {})
    subgoals = goal.get("subgoals", {})

    rule_attempts = []
    for test_key, sg in sorted(subgoals.items()):
        if not isinstance(sg, dict):
            continue
        applied_rule = sg.get("applied_rule")
        test_found = found.get(test_key, {})

        if applied_rule:
            rule_attempts.append({
                "test_key": test_key,
                "rule_id": applied_rule,
                "retrieval_score": test_found.get("retrieval_score", "?"),
                "confidence": test_found.get("confidence", 0),
                "success": sg.get("status") == "solved",
                "failure_reason": None,
            })
        else:
            # rule 적용 실패 또는 미적용
            rule_attempts.append({
                "test_key": test_key,
                "rule_id": None,
                "retrieval_score": None,
                "confidence": 0,
                "success": False,
                "failure_reason": "no matching rule found or all rules failed",
            })

    # matching results 요약
    matching_results_summary = {}
    matching_results = wm.s1.get("matching-results", {})
    for pair_id, mr in matching_results.items():
        if isinstance(mr, dict):
            matching_results_summary[pair_id] = {
                "matched_count": len(mr.get("matched", [])),
                "unmatched_input_count": len(mr.get("unmatched_input", [])),
                "unmatched_output_count": len(mr.get("unmatched_output", [])),
                "branch_count": len(mr.get("branches", [])),
            }

    invariants = wm.s1.get("invariants", [])
    transform_targets = wm.s1.get("transform-targets", [])

    episode = {
        "task_hex": task_hex,
        "timestamp": timestamp,
        "success": success,
        "steps_taken": len(wm.wme_records),
        "rule_attempts": rule_attempts,
        "rules_available": [
            {"rule_id": r["rule"]["rule_id"], "confidence": r["confidence"]}
            for r in active_rules
            if isinstance(r, dict) and "rule" in r
        ],
        "matching_summary": matching_results_summary,
        "invariants": [i["property"] for i in invariants if isinstance(i, dict)],
        "transform_targets": [t["property"] for t in transform_targets if isinstance(t, dict)],
    }

    os.makedirs(episodic_memory_root, exist_ok=True)
    episode_path = os.path.join(
        episodic_memory_root,
        f"episode_{task_hex}_{timestamp}.json",
    )
    with open(episode_path, "w") as f:
        json.dump(episode, f, indent=2)

    return episode_path
