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
    """

    def __init__(self, compare_fn=None):
        super().__init__("compare")
        self._compare_fn = compare_fn or compare

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("has_pending_comparison") is True

    def effect(self, wm):
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
        raise NotImplementedError("ExtractPatternOperator.effect() not implemented.")


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
    """

    def __init__(self, generalize_fn=None, save_fn=None):
        super().__init__("generalize")
        self._generalize_fn = generalize_fn
        self._save_fn = save_fn

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("ready_for_generalization") is True

    def effect(self, wm):
        raise NotImplementedError("GeneralizeOperator.effect() not implemented.")


class PredictOperator(Operator):
    """
    저장된 규칙 중 적합한 것을 꺼내어 test input에 적용한다.
    """

    def __init__(self):
        super().__init__("predict")

    def precondition(self, wm) -> bool:
        state = wm.active
        return state.get("ready_for_prediction") is True

    def effect(self, wm):
        raise NotImplementedError("PredictOperator.effect() not implemented.")


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
        raise NotImplementedError("SubmitOperator.effect() not implemented.")


class VerifyOperator(SubmitOperator):
    """verify 연산의 별칭 operator."""

    def __init__(self):
        super().__init__()
        self.name = "verify"
