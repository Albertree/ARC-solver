"""
active_operators — SOAR Operator 구현체.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[SOAR 강제] 각 operator는 precondition + effect 인터페이스를 따른다.
            effect는 WM을 갱신한다. cycle은 예외·wme 변화로 성공/실패/무변화를 판단.

[설계 자유] 어떤 operator를 둘지, 이름, precondition 조건, effect 내용.
            비교 함수(compare_fn)와 일반화 함수(generalize_fn)를 외부 주입 가능.

이 모듈의 operator들은 인지 수준에서 다음 여섯 연산에 대응하도록 설계된다.

    1. compare  (target_a, target_b, level)
    2. collect  (scope, relation_type)
    3. generalize(targets)
    4. descend  (target, from_level, to_level)
    5. predict  (test_input, rule_ref)
    6. verify   (predicted_output, constraints)

구체 클래스 간 매핑은 다음과 같다.

    - CompareOperator         → compare
    - ExtractPatternOperator  → collect
    - GeneralizeOperator      → generalize
    - DescendOperator         → descend
    - PredictOperator         → predict
    - SubmitOperator/VerifyOperator → verify

즉, SOAR 스타일의 Operator 인터페이스를 유지하면서,
사용자 관점의 고수준 operator 레퍼토리를 그대로 반영한다.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from agent.operators import Operator
from ARCKG.comparison import compare


# ── Object Matching threshold (설정값으로 분리) ──────────────────────────
MATCH_THRESHOLD_NUMERATOR = 5
MATCH_THRESHOLD_DENOMINATOR = 8


class SolveTaskOperator(Operator):
    """
    최상위 ARC 태스크를 해결하기 위한 상위 수준 operator.
    추상 오퍼레이터: intentionally no WM change.
    """

    def __init__(self):
        super().__init__("solve-task")
        self.proposal_preference = "+"

    def precondition(self, wm) -> bool:
        state = wm.active
        return bool(state.get("current-task")) and "goal" in state

    def effect(self, wm):
        return {
            "action": "SolveTask operator가 적용됨 (추상 오퍼레이터)",
            "meaning": "상위 수준 목표만 제시, 구체 동작은 하위 operator가 수행",
            "reason": "current-task가 설정된 상태에서 solve-task가 파이프라인 시작 operator",
            "storage": "WM 변화 없음 (추상 오퍼레이터)",
        }


class SelectTargetOperator(Operator):
    """
    비교 대상(example pair�� G0 vs G1)을 WM에 등록한다.
    """

    def __init__(self):
        super().__init__("select_target")

    def precondition(self, wm) -> bool:
        state = wm.active
        return (
            bool(state.get("current-task"))
            and state.get("needs_target_selection") is True
        )

    def effect(self, wm):
        task = wm.task
        if task is None:
            return None

        pending = []
        for pair in task.example_pairs:
            if pair.output_grid is not None:
                pending.append({
                    "pair_id": pair.node_id,
                    "target_a": pair.input_grid.node_id,
                    "target_b": pair.output_grid.node_id,
                    "level": "GRID",
                    "grid_a": pair.input_grid,
                    "grid_b": pair.output_grid,
                })

        wm.set("pending-compare", pending)
        wm.set("compare-results", [])
        wm.set("needs_target_selection", False)

        pair_ids = [p["pair_id"] for p in pending]
        return {
            "action": f"SelectTarget operator가 {len(pending)}개 example pair의 비교 대상을 등록함",
            "meaning": f"각 example pair의 input(G0) vs output(G1) 비교가 pending 큐에 추가됨. pairs: {pair_ids}",
            "reason": "current-task가 설정되고 아직 비교 대상이 없었으므로 SelectTarget이 유일한 후보",
            "storage": "WM 슬롯 (S1 ^pending-compare), (S1 ^compare-results)",
        }


class CompareOperator(Operator):
    """
    대기 중인 비교 한 건을 수행하고 결과를 WM에 추가한다.
    GRID/OBJECT 레벨을 모두 처리한다.
    all_comparisons_done 후 Object Matching도 수행한다.
    """

    def __init__(self, compare_fn=None):
        super().__init__("compare")
        self._compare_fn = compare_fn or compare

    def precondition(self, wm) -> bool:
        state = wm.active
        if state.get("has_pending_comparison") is True:
            return True
        if (state.get("all_comparisons_done") is True
                and state.get("matching-results") is None):
            return True
        return False

    def effect(self, wm):
        # 모든 비교 완료 후 Object Matching 수행
        if (wm.get("all_comparisons_done") is True
                and wm.get("matching-results") is None):
            return self._do_object_matching(wm)

        pending = wm.get("pending-compare")
        if not pending:
            return None

        item = pending.pop(0)
        level = item["level"]

        if level == "GRID":
            return self._compare_grid(wm, item, pending)
        elif level == "OBJECT":
            return self._compare_object(wm, item, pending)
        return None

    def _compare_grid(self, wm, item, pending):
        """Grid 레벨 비교 수행."""
        grid_a = item["grid_a"]
        grid_b = item["grid_b"]
        pair_id = item["pair_id"]

        result = self._compare_fn(
            grid_a, grid_b,
            save=True,
            semantic_memory_root="semantic_memory",
        )

        result_entry = {
            "pair_id": pair_id,
            "id1": grid_a.node_id,
            "id2": grid_b.node_id,
            "level": "GRID",
            "result": result,
        }

        compare_results = wm.get("compare-results") or []
        compare_results.append(result_entry)
        wm.set("compare-results", compare_results)

        # Grid contents가 DIFF면 Object 레벨 비교를 pending에 추가 (pruning)
        grid_result = result.get("result", {})
        cat = grid_result.get("category", {})
        contents_type = cat.get("contents", {}).get("type", "DIFF")

        note = ""
        if contents_type == "DIFF":
            objects_a = grid_a.objects
            objects_b = grid_b.objects
            for oa in objects_a:
                for ob in objects_b:
                    pending.append({
                        "pair_id": pair_id,
                        "target_a": oa.node_id,
                        "target_b": ob.node_id,
                        "level": "OBJECT",
                        "obj_a": oa,
                        "obj_b": ob,
                    })
            note = (
                f" contents=DIFF이므로 Object 레벨 "
                f"{len(objects_a)}x{len(objects_b)} 비교 추가"
            )
        else:
            note = " contents=COMM이므로 Object 레벨 비교 생략 (pruning)"

        wm.set("pending-compare", pending)

        score = grid_result.get("score", "?/?")
        edge_id = f"E_{grid_a.node_id}-{grid_b.node_id}"
        save_path = f"semantic_memory/N_T{wm.task.task_hex}/{edge_id}.json"

        return {
            "action": f"Compare operator가 {grid_a.node_id}와 {grid_b.node_id}를 GRID 레벨에서 비교함",
            "meaning": f"1차 relation 엣지 생성. score={score}, type={grid_result.get('type', '?')}.{note}",
            "reason": f"pending-compare에 {pair_id}의 GRID 비교 항목이 있었으므로 Compare가 선택됨",
            "storage": f"{save_path}",
        }

    def _compare_object(self, wm, item, pending):
        """Object 레벨 비교 수행."""
        obj_a = item["obj_a"]
        obj_b = item["obj_b"]
        pair_id = item["pair_id"]

        result = self._compare_fn(
            obj_a, obj_b,
            save=True,
            semantic_memory_root="semantic_memory",
        )

        result_entry = {
            "pair_id": pair_id,
            "id1": obj_a.node_id,
            "id2": obj_b.node_id,
            "level": "OBJECT",
            "result": result,
        }

        compare_results = wm.get("compare-results") or []
        compare_results.append(result_entry)
        wm.set("compare-results", compare_results)
        wm.set("pending-compare", pending)

        obj_result = result.get("result", {})
        score = obj_result.get("score", "?/?")
        edge_id = f"E_{obj_a.node_id}-{obj_b.node_id}"
        save_path = f"semantic_memory/N_T{wm.task.task_hex}/{edge_id}.json"

        return {
            "action": f"Compare operator가 {obj_a.node_id}와 {obj_b.node_id}를 OBJECT 레벨에서 비교함",
            "meaning": f"Object 비교 결과. score={score}, type={obj_result.get('type', '?')}",
            "reason": f"pending-compare에 {pair_id}의 OBJECT 비교 항목이 있었으므로 Compare가 선택됨",
            "storage": f"{save_path}",
        }


    def _do_object_matching(self, wm):
        """
        Object Matching: M×N 비교 결과를 pair별로 그룹화하고,
        score 내림차순 정렬 → threshold(5/8) 분기 → 동점 처리 → branching.
        """
        compare_results = wm.get("compare-results") or []
        task = wm.task

        # pair별로 OBJECT 레벨 결과 그룹화
        pair_obj_results = {}
        for entry in compare_results:
            if entry["level"] != "OBJECT":
                continue
            pid = entry["pair_id"]
            if pid not in pair_obj_results:
                pair_obj_results[pid] = []
            pair_obj_results[pid].append(entry)

        matching_results = {}
        interpretation_parts = []

        for pair_id, obj_results in pair_obj_results.items():
            # score 파싱 및 내림차순 정렬
            scored = []
            for entry in obj_results:
                res = entry["result"].get("result", {})
                score_str = res.get("score", "0/0")
                num, denom = _parse_score(score_str)
                scored.append({
                    "id1": entry["id1"],
                    "id2": entry["id2"],
                    "score": score_str,
                    "score_num": num,
                    "score_denom": denom,
                    "score_ratio": num / denom if denom > 0 else 0,
                    "result": entry["result"],
                })
            scored.sort(key=lambda x: x["score_ratio"], reverse=True)

            # threshold 분기: > 5/8 = matching, <= 5/8 = non-matching
            threshold = MATCH_THRESHOLD_NUMERATOR / MATCH_THRESHOLD_DENOMINATOR
            matched = []
            unmatched = []
            used_a = set()
            used_b = set()

            for item in scored:
                if item["score_ratio"] > threshold:
                    # greedy matching: 이미 매칭된 object는 제외
                    if item["id1"] not in used_a and item["id2"] not in used_b:
                        matched.append(item)
                        used_a.add(item["id1"])
                        used_b.add(item["id2"])
                    else:
                        # 동점 처리: 1차·2차 relation 추가 확인
                        # 이미 사용된 object와 동일 score면 branching 후보
                        unmatched.append(item)
                else:
                    unmatched.append(item)

            # 동점 처리: matched 중 동일 score 쌍 확인
            branches = []
            score_groups = {}
            for item in matched:
                s = item["score_str"] if "score_str" in item else item["score"]
                if s not in score_groups:
                    score_groups[s] = []
                score_groups[s].append(item)
            for s, group in score_groups.items():
                if len(group) > 1:
                    branches.append({
                        "score": s,
                        "candidates": [
                            {"id1": g["id1"], "id2": g["id2"]}
                            for g in group
                        ],
                    })

            # creation/deletion/split/merge 케이스 분류
            all_obj_a = set()
            all_obj_b = set()
            for entry in obj_results:
                all_obj_a.add(entry["id1"])
                all_obj_b.add(entry["id2"])

            unmatched_a = all_obj_a - used_a  # G0 objects not matched → deleted
            unmatched_b = all_obj_b - used_b  # G1 objects not matched → created

            matching_results[pair_id] = {
                "matched": [
                    {"id1": m["id1"], "id2": m["id2"], "score": m["score"]}
                    for m in matched
                ],
                "unmatched_input": list(unmatched_a),   # deletion candidates
                "unmatched_output": list(unmatched_b),   # creation candidates
                "branches": branches,
                "all_scores_sorted": [
                    {"id1": s["id1"], "id2": s["id2"], "score": s["score"]}
                    for s in scored
                ],
            }

            n_match = len(matched)
            n_del = len(unmatched_a)
            n_cre = len(unmatched_b)
            n_branch = len(branches)
            interpretation_parts.append(
                f"{pair_id}: {n_match} matched, "
                f"{n_del} deleted, {n_cre} created, "
                f"{n_branch} branching points"
            )

        wm.set("matching-results", matching_results)

        return {
            "action": f"Object Matching 수행: {len(pair_obj_results)}개 pair의 M×N 결과 처리",
            "meaning": "; ".join(interpretation_parts),
            "reason": "all_comparisons_done이 True이고 matching-results가 아직 없었으므로",
            "storage": "WM 슬롯 (S1 ^matching-results)",
        }


def _parse_score(score_str: str) -> tuple[int, int]:
    """'X/N' 형식의 score를 (numerator, denominator) 튜플로 파싱."""
    try:
        parts = score_str.split("/")
        return int(parts[0]), int(parts[1])
    except (ValueError, IndexError):
        return 0, 0


class ExtractPatternOperator(Operator):
    """
    비교 결과에서 COMM/DIFF 패턴을 WM triplet으로 정리한다.
    score 가중치 기반으로 invariant를 결정한다.
    """

    def __init__(self):
        super().__init__("extract_pattern")

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("ready_for_pattern_extraction") is True

    def effect(self, wm):
        matching_results = wm.get("matching-results")
        compare_results = wm.get("compare-results") or []
        if not matching_results:
            return None

        # Object 레벨 비교 결과를 (id1, id2) → result로 인덱싱
        obj_result_index = {}
        for entry in compare_results:
            if entry["level"] == "OBJECT":
                key = (entry["id1"], entry["id2"])
                obj_result_index[key] = entry["result"]

        # 8개 OBJECT property
        obj_properties = [
            "area", "color", "coordinate", "method",
            "position", "shape", "size", "symmetry",
        ]

        # pair별 matched 쌍에서 COMM/DIFF 패턴 추출 (score 내림차순으로 이미 정렬됨)
        all_pair_patterns = {}
        for pair_id, mr in matching_results.items():
            pair_patterns = []
            for match in mr["matched"]:
                key = (match["id1"], match["id2"])
                result = obj_result_index.get(key)
                if not result:
                    continue
                res = result.get("result", {})
                cat = res.get("category", {})
                score = match["score"]

                pattern = {"score": score, "id1": match["id1"], "id2": match["id2"]}
                for prop in obj_properties:
                    prop_result = cat.get(prop, {})
                    prop_type = prop_result.get("type", "DIFF")
                    pattern[prop] = prop_type
                pair_patterns.append(pattern)
            all_pair_patterns[pair_id] = pair_patterns

        # score 가중치 기반 invariant/transformation 결정
        # 여러 쌍에서 반복적으로 COMM인 property → invariant
        # 특정 쌍에서만 DIFF인 property → transformation 대상 후보
        property_comm_counts = {prop: 0 for prop in obj_properties}
        property_diff_counts = {prop: 0 for prop in obj_properties}
        total_matched_pairs = 0

        for pair_id, patterns in all_pair_patterns.items():
            for pattern in patterns:
                total_matched_pairs += 1
                num, denom = _parse_score(pattern["score"])
                weight = num / denom if denom > 0 else 0
                for prop in obj_properties:
                    if pattern[prop] == "COMM":
                        property_comm_counts[prop] += weight
                    else:
                        property_diff_counts[prop] += weight

        invariants = []
        transform_targets = []
        for prop in obj_properties:
            comm = property_comm_counts[prop]
            diff = property_diff_counts[prop]
            total = comm + diff
            if total == 0:
                continue
            if comm > diff:
                invariants.append({"property": prop, "comm_weight": comm, "diff_weight": diff})
            elif diff > 0:
                transform_targets.append({"property": prop, "comm_weight": comm, "diff_weight": diff})

        wm.set("invariants", invariants)
        wm.set("transform-targets", transform_targets)
        wm.set("pair-patterns", all_pair_patterns)

        inv_names = [i["property"] for i in invariants]
        tf_names = [t["property"] for t in transform_targets]

        return {
            "action": f"ExtractPattern operator가 {total_matched_pairs}개 matched 쌍에서 패턴 추출",
            "meaning": f"invariants: {inv_names}, transformation targets: {tf_names}",
            "reason": "matching-results가 완성되고 아직 invariants가 없었으므로 ExtractPattern이 선택됨",
            "storage": "WM 슬롯 (S1 ^invariants), (S1 ^transform-targets), (S1 ^pair-patterns)",
        }


class DescendOperator(Operator):
    """
    GRID/OBJECT/PIXEL 등 상위 레벨 분석에서 impasse가 발생했을 때
    더 낮은 레벨의 노드/관계를 WM으로 끌어와 추가 비교를 가능하게 한다.
    """

    def __init__(self):
        super().__init__("descend")

    def precondition(self, wm) -> bool:
        raise NotImplementedError("DescendOperator.precondition() not implemented.")

    def effect(self, wm):
        raise NotImplementedError("DescendOperator.effect() not implemented.")


class GeneralizeOperator(Operator):
    """
    WM에 모인 불변/차이 패턴을 일반화 함수에 전달해
    추상 규칙을 생성하고 procedural_memory에 저장한다.
    2차 compare로 pair 간 공통 패턴을 추출하고 anti-unification을 수행한다.
    """

    def __init__(self, generalize_fn=None, save_fn=None):
        super().__init__("generalize")
        self._generalize_fn = generalize_fn
        self._save_fn = save_fn

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("ready_for_generalization") is True

    def effect(self, wm):
        import json
        import os

        compare_results = wm.get("compare-results") or []
        matching_results = wm.get("matching-results") or {}
        invariants = wm.get("invariants") or []
        transform_targets = wm.get("transform-targets") or []
        task = wm.task

        # 1. pair별 1차 GRID 비교 결과 수집
        pair_grid_results = {}
        for entry in compare_results:
            if entry["level"] == "GRID":
                pair_grid_results[entry["pair_id"]] = entry["result"]

        pair_ids = list(pair_grid_results.keys())
        if len(pair_ids) < 2:
            # 단일 pair면 2차 비교 불가, 1차 결과로만 규칙 생성
            return self._single_pair_rule(wm, pair_ids, invariants, transform_targets)

        # 2. 2차 엣지 생성: compare(pair0_result, pair1_result)
        second_order_results = []
        for i in range(len(pair_ids)):
            for j in range(i + 1, len(pair_ids)):
                result_i = pair_grid_results[pair_ids[i]]
                result_j = pair_grid_results[pair_ids[j]]
                second_order = compare(
                    result_i, result_j,
                    save=True,
                    semantic_memory_root="semantic_memory",
                )
                second_order_results.append({
                    "pair_i": pair_ids[i],
                    "pair_j": pair_ids[j],
                    "result": second_order,
                })

        # 3. Anti-unification: 2차 비교에서 COMM → signature, DIFF → "?"
        # signature 구축
        signature = {}
        transformation_targets = []
        for inv in invariants:
            signature[inv["property"]] = {"type": "COMM"}
        for tf in transform_targets:
            signature[tf["property"]] = {"type": "DIFF"}
            transformation_targets.append(tf["property"])

        # 2차 비교 결과로 signature 보강
        for so in second_order_results:
            so_result = so["result"].get("result", {})
            so_cat = so_result.get("category", {})
            # category 내부의 각 property별 2차 비교 결과 확인
            for prop_name, prop_result in so_cat.items():
                if isinstance(prop_result, dict):
                    prop_type = prop_result.get("type", "DIFF")
                    if prop_name in signature:
                        # 2차에서 DIFF면 변수로 치환
                        if prop_type == "DIFF":
                            signature[prop_name] = {"type": "DIFF", "variable": "?"}

        # 4. procedural_memory에 JSON 저장
        rule_id = self._next_rule_id()
        rule = {
            "rule_id": rule_id,
            "order": 2,
            "signature": signature,
            "transformation": {
                "target": transformation_targets[0] if transformation_targets else "?",
                "action": "DIFF",
                "variable": "?",
            },
            "source_pairs": pair_ids,
            "confidence": len(pair_ids),
        }

        os.makedirs("procedural_memory", exist_ok=True)
        rule_path = f"procedural_memory/{rule_id}.json"
        with open(rule_path, "w") as f:
            json.dump(rule, f, indent=2)

        # WM에 active_rules 등록
        wm.set("active_rules", [{
            "ref": rule_path,
            "confidence": rule["confidence"],
            "rule": rule,
        }])

        return {
            "action": f"Generalize operator가 {len(pair_ids)}개 pair에서 2차 compare 후 anti-unification 수행",
            "meaning": (
                f"규칙 {rule_id} 생성: signature={list(signature.keys())}, "
                f"transformation target={transformation_targets}, confidence={rule['confidence']}"
            ),
            "reason": "invariants와 transform-targets가 완성되고 아직 active_rules가 없었으므로",
            "storage": f"procedural_memory/{rule_id}.json, WM 슬롯 (S1 ^active_rules)",
        }

    def _single_pair_rule(self, wm, pair_ids, invariants, transform_targets):
        """단일 pair인 경우: 2차 비교 없이 1차 패턴으로 규칙 생성 (confidence=1)."""
        import json, os

        signature = {}
        transformation_targets_list = []
        for inv in invariants:
            signature[inv["property"]] = {"type": "COMM"}
        for tf in transform_targets:
            signature[tf["property"]] = {"type": "DIFF", "variable": "?"}
            transformation_targets_list.append(tf["property"])

        rule_id = self._next_rule_id()
        rule = {
            "rule_id": rule_id,
            "order": 1,
            "signature": signature,
            "transformation": {
                "target": transformation_targets_list[0] if transformation_targets_list else "?",
                "action": "DIFF",
                "variable": "?",
            },
            "source_pairs": pair_ids,
            "confidence": 1,
        }

        os.makedirs("procedural_memory", exist_ok=True)
        rule_path = f"procedural_memory/{rule_id}.json"
        with open(rule_path, "w") as f:
            json.dump(rule, f, indent=2)

        wm.set("active_rules", [{
            "ref": rule_path,
            "confidence": rule["confidence"],
            "rule": rule,
        }])

        return {
            "action": f"Generalize operator가 단일 pair에서 1차 규칙 생성 (confidence=1)",
            "meaning": f"규칙 {rule_id} 생성: signature={list(signature.keys())}",
            "reason": "pair가 1개뿐이므로 2차 비교 없이 1차 패턴으로 규칙 생성",
            "storage": f"procedural_memory/{rule_id}.json, WM 슬롯 (S1 ^active_rules)",
        }

    @staticmethod
    def _next_rule_id() -> str:
        """procedural_memory/ 내 기존 규칙 수를 기반으로 다음 rule_id를 생성."""
        import os, glob
        existing = glob.glob("procedural_memory/R_*.json")
        n = len(existing) + 1
        return f"R_{n:03d}"


class PredictOperator(Operator):
    """
    저장된 규칙 중 적합한 것을 꺼내어 test input에 적용한다.
    3차 compare로 retrieval, confidence 기반 우선순위, 실패 시 다음 후보.
    """

    def __init__(self):
        super().__init__("predict")

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("ready_for_prediction") is True

    def effect(self, wm):
        from ARCKG.comparison import compare_for_retrieval

        active_rules = wm.get("active_rules") or []
        task = wm.task
        if not active_rules or not task:
            return None

        goal = wm.get("goal") or {}
        subgoals = goal.get("subgoals") or {}

        # pending test subgoal 찾기
        test_key = None
        test_sg = None
        for k, sg in sorted(subgoals.items()):
            if isinstance(sg, dict) and sg.get("status") == "pending":
                test_key = k
                test_sg = sg
                break
        if not test_sg:
            return None

        test_input = test_sg.get("input_grid")
        if not test_input:
            return None

        # 1. 새 문제의 1차 pattern 구성
        # 분석이 완료된 경우 invariant/transform-target 사용
        # 분석이 없는 경우 (pre-loaded rules) rule의 signature 구조를 사용
        invariants = wm.get("invariants") or []
        transform_targets = wm.get("transform-targets") or []

        problem_pattern = {}
        if invariants or transform_targets:
            for inv in invariants:
                problem_pattern[inv["property"]] = {"type": "COMM"}
            for tf in transform_targets:
                problem_pattern[tf["property"]] = {"type": "DIFF"}
        else:
            # 분석 없이 retrieval: 모든 property를 rule signature에서 가져와 매칭
            # 이 경우 모든 rule의 signature type과 정확히 일치하는지 확인
            for rule_entry in active_rules:
                sig = rule_entry.get("rule", {}).get("signature", {})
                for prop, val in sig.items():
                    if prop not in problem_pattern:
                        problem_pattern[prop] = {"type": val.get("type", "DIFF")}

        # 2. 3차 compare: retrieval
        retrieval_candidates = []
        for rule_entry in active_rules:
            rule = rule_entry["rule"]
            signature = rule.get("signature", {})
            confidence = rule.get("confidence", 0)

            # compare_for_retrieval: type만 대조, wildcard 처리
            retrieval_result = compare_for_retrieval(problem_pattern, signature)
            ret_score_str = retrieval_result.get("score", "0/0")
            num, denom = _parse_score(ret_score_str)
            ret_ratio = num / denom if denom > 0 else 0

            retrieval_candidates.append({
                "rule": rule,
                "rule_ref": rule_entry["ref"],
                "retrieval_score": ret_score_str,
                "retrieval_ratio": ret_ratio,
                "confidence": confidence,
                "retrieval_result": retrieval_result,
            })

        # retrieval_score 내림차순, 동점이면 confidence 내림차순
        retrieval_candidates.sort(
            key=lambda x: (x["retrieval_ratio"], x["confidence"]),
            reverse=True,
        )

        # 3차 엣지를 semantic_memory에 기록
        import json, os
        for cand in retrieval_candidates:
            edge_path = f"semantic_memory/N_T{task.task_hex}/retrieval_{cand['rule']['rule_id']}.json"
            os.makedirs(os.path.dirname(edge_path), exist_ok=True)
            with open(edge_path, "w") as f:
                json.dump({
                    "type": "3rd_order_retrieval",
                    "rule_id": cand["rule"]["rule_id"],
                    "retrieval_score": cand["retrieval_score"],
                    "result": cand["retrieval_result"],
                }, f, indent=2)

        # 3. Application: 우선순위 높은 rule부터 시도
        from agent.apply_rule import apply_learned_rule

        applied_rule = None
        predicted_grid = None
        for cand in retrieval_candidates:
            rule = cand["rule"]
            transformation = rule.get("transformation", {})
            target_prop = transformation.get("target")

            if target_prop:
                # 규칙 적용: 실제 output grid 생성
                predicted_grid = apply_learned_rule(task, wm)
                if predicted_grid is not None:
                    applied_rule = cand
                    break

        if not applied_rule:
            return {
                "action": "Predict operator: 적용 가능한 규칙 없음",
                "meaning": "모든 규칙의 retrieval_score가 0이거나 적용 실패",
                "reason": "active_rules가 존재하고 pending test subgoal이 있었으므로 Predict 선택",
                "storage": "WM 변화 없음",
            }

        # test subgoal 상태 갱신
        test_sg["status"] = "solved"
        test_sg["applied_rule"] = applied_rule["rule"]["rule_id"]
        test_sg["retrieval_score"] = applied_rule["retrieval_score"]
        test_sg["predicted_output"] = predicted_grid

        # found 기록
        found = wm.get("found") or {}
        found[test_key] = {
            "rule_id": applied_rule["rule"]["rule_id"],
            "retrieval_score": applied_rule["retrieval_score"],
            "confidence": applied_rule["confidence"],
            "predicted_output": predicted_grid,
        }
        wm.set("found", found)
        wm.set("goal", goal)

        return {
            "action": (
                f"Predict operator가 규칙 {applied_rule['rule']['rule_id']}을 "
                f"test subgoal {test_key}에 적용 (retrieval_score={applied_rule['retrieval_score']})"
            ),
            "meaning": (
                f"3차 compare로 {len(retrieval_candidates)}개 규칙 검색. "
                f"최우선 규칙 {applied_rule['rule']['rule_id']} "
                f"(confidence={applied_rule['confidence']}) 적용"
            ),
            "reason": "active_rules가 존재하고 pending test subgoal이 있었으므로 Predict 선택",
            "storage": (
                f"semantic_memory/N_T{task.task_hex}/retrieval_{applied_rule['rule']['rule_id']}.json, "
                f"WM 슬롯 (S1 ^found), goal.subgoals.{test_key}.status=solved"
            ),
        }


class SubmitOperator(Operator):
    """
    모든 test subgoal이 해결되었으면 goal_satisfied를 만족시킨다.
    """

    def __init__(self):
        super().__init__("submit")

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("all_outputs_found") is True

    def effect(self, wm):
        goal = wm.get("goal") or {}
        found = wm.get("found") or {}
        wm.set("goal", goal)

        return {
            "action": "Submit operator: 모든 test subgoal이 해결됨",
            "meaning": f"총 {len(found)}개 test subgoal 완료. 규칙 적용 결과 제출",
            "reason": "all_outputs_found가 True이므로 Submit 선택",
            "storage": "WM 슬롯 (S1 ^goal) 갱신",
        }


class VerifyOperator(SubmitOperator):
    """verify 연산의 별칭 operator."""

    def __init__(self):
        super().__init__()
        self.name = "verify"
