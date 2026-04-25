"""
apply_rule — 학습된 규칙을 test input에 적용하여 output grid를 생성한다.

compare 결과에서 발견한 transformation을 실제 grid에 적용하는 모듈.
transformation 함수를 하드코딩하지 않고, example pair에서 패턴을 추출하여 적용한다.
"""

from __future__ import annotations

import copy
from typing import Any


def apply_learned_rule(task, wm) -> list[list[int]] | None:
    """
    example pair에서 학습한 변환 규칙을 test input에 적용하여
    predicted output grid를 반환한다.

    지원하는 변환 유형:
    1. color 변환: object 색상 변경 (ordering 기반)
    2. coordinate/position 변환: object 위치 이동
    """
    matching_results = wm.get("matching-results") or {}
    transform_targets = wm.get("transform-targets") or []

    # transform_targets가 없으면 active_rules의 signature에서 추출
    if not transform_targets:
        active_rules = wm.get("active_rules") or []
        for rule_entry in active_rules:
            rule = rule_entry.get("rule", {})
            sig = rule.get("signature", {})
            for prop, val in sig.items():
                if isinstance(val, dict) and val.get("type") == "DIFF":
                    transform_targets.append({"property": prop})

    # matching_results가 없으면 example pair에서 직접 matching 수행
    if not matching_results:
        matching_results = _build_matching_from_examples(task)

    if not transform_targets:
        return None

    target_props = [t["property"] for t in transform_targets]

    # 변환 유형 판별 및 적용
    if "color" in target_props and "coordinate" not in target_props and "position" not in target_props:
        return _apply_color_transformation(task, matching_results)
    elif "coordinate" in target_props or "position" in target_props:
        return _apply_position_transformation(task, matching_results, target_props)
    else:
        # 일반 변환: example에서 직접 패턴 추출 시도
        return _apply_general_transformation(task, matching_results, target_props)


# ---------------------------------------------------------------------------
# Matching fallback (규칙만 로드된 경우 example에서 직접 매칭)
# ---------------------------------------------------------------------------

def _build_matching_from_examples(task) -> dict:
    """
    분석 단계 없이 example pair에서 직접 object matching을 수행한다.
    input/output object를 1:1 greedy matching한다.
    """
    from ARCKG.comparison import compare

    matching_results = {}
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        input_objs = pair.input_grid.objects
        output_objs = pair.output_grid.objects

        # M×N compare, score 계산
        scored = []
        for io in input_objs:
            for oo in output_objs:
                result = compare(io, oo)
                res = result.get("result", {})
                score_str = res.get("score", "0/0")
                parts = score_str.split("/")
                try:
                    num, denom = int(parts[0]), int(parts[1])
                except (ValueError, IndexError):
                    num, denom = 0, 0
                scored.append({
                    "id1": io.node_id,
                    "id2": oo.node_id,
                    "score": score_str,
                    "ratio": num / denom if denom > 0 else 0,
                })

        # greedy matching (score 내림차순)
        scored.sort(key=lambda x: x["ratio"], reverse=True)
        used_a, used_b = set(), set()
        matched = []
        for item in scored:
            if item["id1"] not in used_a and item["id2"] not in used_b:
                matched.append(item)
                used_a.add(item["id1"])
                used_b.add(item["id2"])

        matching_results[pair.node_id] = {
            "matched": [{"id1": m["id1"], "id2": m["id2"], "score": m["score"]} for m in matched],
            "unmatched_input": [o.node_id for o in input_objs if o.node_id not in used_a],
            "unmatched_output": [o.node_id for o in output_objs if o.node_id not in used_b],
            "branches": [],
        }

    return matching_results


# ---------------------------------------------------------------------------
# Color Transformation (08ed6ac7 유형)
# ---------------------------------------------------------------------------

def _apply_color_transformation(task, matching_results):
    """object 색상을 ordering 기반으로 변환."""
    example_patterns = _extract_color_patterns(task, matching_results)
    if not example_patterns:
        return None

    ordering_criterion, color_sequence = _discover_color_ordering(example_patterns)
    if ordering_criterion is None:
        return None

    for test_pair in task.test_pairs:
        test_grid = test_pair.input_grid
        predicted = _apply_color_to_test(test_grid, ordering_criterion, color_sequence)
        if predicted is not None:
            return predicted
    return None


def _extract_color_patterns(task, matching_results):
    patterns = []
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        pair_matching = matching_results.get(pair.node_id, {})
        matched = pair_matching.get("matched", [])
        input_objs = {o.node_id: o for o in pair.input_grid.objects}
        output_objs = {o.node_id: o for o in pair.output_grid.objects}

        pair_data = []
        for match in matched:
            in_obj = input_objs.get(match["id1"])
            out_obj = output_objs.get(match["id2"])
            if not in_obj or not out_obj:
                continue
            if in_obj.color == out_obj.color:
                continue
            pair_data.append({
                "input_area": len(in_obj.coordinate),
                "input_height": len(in_obj.colorgrid),
                "input_width": len(in_obj.colorgrid[0]) if in_obj.colorgrid else 0,
                "input_color": in_obj.color,
                "output_color": out_obj.color,
                "input_pos_row": in_obj.pos[0],
                "input_pos_col": in_obj.pos[1],
            })
        if pair_data:
            patterns.append(pair_data)
    return patterns


def _discover_color_ordering(example_patterns):
    criteria = [
        ("input_area", True),
        ("input_height", True),
        ("input_pos_col", False),
        ("input_pos_row", False),
    ]
    for criterion_key, reverse in criteria:
        consistent = True
        reference_sequence = None
        for pair_data in example_patterns:
            sorted_data = sorted(pair_data, key=lambda x: x[criterion_key], reverse=reverse)
            sequence = [d["output_color"] for d in sorted_data]
            if reference_sequence is None:
                reference_sequence = sequence
            elif sequence != reference_sequence:
                consistent = False
                break
        if consistent and reference_sequence:
            return criterion_key, reference_sequence
    if example_patterns:
        pair_data = example_patterns[0]
        sorted_data = sorted(pair_data, key=lambda x: x["input_area"], reverse=True)
        sequence = [d["output_color"] for d in sorted_data]
        return "input_area", sequence
    return None, None


def _apply_color_to_test(test_grid, ordering_criterion, color_sequence):
    test_objects = test_grid.objects
    if not test_objects:
        return None
    target_objects = [obj for obj in test_objects if obj.color != 0]
    if not target_objects:
        return None

    reverse = ordering_criterion in ("input_area", "input_height")
    key_map = {
        "input_area": lambda o: len(o.coordinate),
        "input_height": lambda o: len(o.colorgrid),
        "input_width": lambda o: len(o.colorgrid[0]) if o.colorgrid else 0,
        "input_pos_col": lambda o: o.pos[1],
        "input_pos_row": lambda o: o.pos[0],
    }
    sort_key = key_map.get(ordering_criterion, key_map["input_area"])
    sorted_objects = sorted(target_objects, key=sort_key, reverse=reverse)

    output = copy.deepcopy(test_grid.raw)
    for rank, obj in enumerate(sorted_objects):
        new_color = color_sequence[rank] if rank < len(color_sequence) else rank + 1
        for r, c in obj.coordinate:
            if 0 <= r < len(output) and 0 <= c < len(output[0]):
                output[r][c] = new_color
    return output


# ---------------------------------------------------------------------------
# Position/Coordinate Transformation (easy0014 유형)
# ---------------------------------------------------------------------------

def _apply_position_transformation(task, matching_results, target_props):
    """
    object 위치를 변환한다.
    example pair에서 input→output 위치 변화 패턴을 추출하고 test에 적용한다.
    """
    # example pair에서 위치 변환 패턴 추출
    move_patterns = []
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        pair_matching = matching_results.get(pair.node_id, {})
        matched = pair_matching.get("matched", [])
        input_objs = {o.node_id: o for o in pair.input_grid.objects}
        output_objs = {o.node_id: o for o in pair.output_grid.objects}

        grid_h = pair.input_grid.height
        grid_w = pair.input_grid.width

        for match in matched:
            in_obj = input_objs.get(match["id1"])
            out_obj = output_objs.get(match["id2"])
            if not in_obj or not out_obj:
                continue

            in_coords = set(tuple(c) for c in in_obj.coordinate)
            out_coords = set(tuple(c) for c in out_obj.coordinate)
            if in_coords == out_coords:
                continue  # 위치 변화 없음

            move_patterns.append({
                "input_pos": in_obj.pos,
                "output_pos": out_obj.pos,
                "input_coords": sorted(in_obj.coordinate),
                "output_coords": sorted(out_obj.coordinate),
                "input_color": in_obj.color,
                "output_color": out_obj.color,
                "input_colorgrid": in_obj.colorgrid,
                "grid_h": grid_h,
                "grid_w": grid_w,
                "obj_h": len(in_obj.colorgrid),
                "obj_w": len(in_obj.colorgrid[0]) if in_obj.colorgrid else 0,
            })

    if not move_patterns:
        return None

    # 패턴 분석: 모든 example에서 공통된 이동 규칙 발견
    move_rule = _discover_move_rule(move_patterns)
    if move_rule is None:
        return None

    # test input에 적용
    for test_pair in task.test_pairs:
        predicted = _apply_move_to_test(test_pair.input_grid, move_rule)
        if predicted is not None:
            return predicted
    return None


def _discover_move_rule(move_patterns: list[dict]) -> dict | None:
    """
    위치 변환 규칙을 발견한다.

    지원 패턴:
    1. absolute: 모든 object가 같은 절대 위치로 이동
    2. relative: 모든 object가 같은 방향/거리로 이동
    3. anchor: grid의 특정 위치(코너 등)로 이동
    """
    if not move_patterns:
        return None

    # 1. absolute 이동: 모든 output_pos가 동일한지 확인
    output_positions = [tuple(p["output_pos"]) for p in move_patterns]
    if len(set(output_positions)) == 1:
        # 모든 example에서 같은 절대 위치로 이동
        # 그런데 grid 크기 대비 상대 위치인지 확인
        abs_pos = output_positions[0]
        # grid 코너 체크
        for p in move_patterns:
            gh, gw = p["grid_h"], p["grid_w"]
            oh, ow = p["obj_h"], p["obj_w"]
            if abs_pos == (gh - oh, gw - ow):
                # 우하단 코너 정렬
                return {"type": "anchor", "anchor": "bottom_right"}
            elif abs_pos == (0, 0):
                return {"type": "anchor", "anchor": "top_left"}
            elif abs_pos == (0, gw - ow):
                return {"type": "anchor", "anchor": "top_right"}
            elif abs_pos == (gh - oh, 0):
                return {"type": "anchor", "anchor": "bottom_left"}
        # 그냥 절대 위치
        return {"type": "absolute", "target_pos": abs_pos}

    # 2. relative 이동: delta가 동일한지 확인
    deltas = []
    for p in move_patterns:
        dr = p["output_pos"][0] - p["input_pos"][0]
        dc = p["output_pos"][1] - p["input_pos"][1]
        deltas.append((dr, dc))
    if len(set(deltas)) == 1:
        return {"type": "relative", "delta": deltas[0]}

    # 3. anchor 패턴: output이 grid 경계에 정렬되는지 확인
    # output_pos가 grid 크기에 의존적인지 체크
    all_bottom_right = True
    for p in move_patterns:
        gh, gw = p["grid_h"], p["grid_w"]
        oh, ow = p["obj_h"], p["obj_w"]
        expected_pos = (gh - oh, gw - ow)
        if tuple(p["output_pos"]) != expected_pos:
            all_bottom_right = False
            break
    if all_bottom_right:
        return {"type": "anchor", "anchor": "bottom_right"}

    return None


def _apply_move_to_test(test_grid, move_rule: dict) -> list[list[int]] | None:
    """이동 규칙을 test input에 적용하여 output grid를 생성."""
    test_objects = test_grid.objects
    if not test_objects:
        return None

    target_objects = [obj for obj in test_objects if obj.color != 0]
    if not target_objects:
        return None

    grid_h = test_grid.height
    grid_w = test_grid.width
    output = [[0] * grid_w for _ in range(grid_h)]  # 빈 grid

    for obj in target_objects:
        obj_h = len(obj.colorgrid)
        obj_w = len(obj.colorgrid[0]) if obj.colorgrid else 0

        if move_rule["type"] == "anchor":
            anchor = move_rule["anchor"]
            if anchor == "bottom_right":
                new_row = grid_h - obj_h
                new_col = grid_w - obj_w
            elif anchor == "top_left":
                new_row, new_col = 0, 0
            elif anchor == "top_right":
                new_row = 0
                new_col = grid_w - obj_w
            elif anchor == "bottom_left":
                new_row = grid_h - obj_h
                new_col = 0
            else:
                continue
        elif move_rule["type"] == "absolute":
            new_row, new_col = move_rule["target_pos"]
        elif move_rule["type"] == "relative":
            dr, dc = move_rule["delta"]
            new_row = obj.pos[0] + dr
            new_col = obj.pos[1] + dc
        else:
            continue

        # object의 colorgrid를 새 위치에 그린다
        for r, row in enumerate(obj.colorgrid):
            for c, cell in enumerate(row):
                if cell != 13:  # 투명이 아닌 셀
                    out_r = new_row + r
                    out_c = new_col + c
                    if 0 <= out_r < grid_h and 0 <= out_c < grid_w:
                        output[out_r][out_c] = cell

    return output


# ---------------------------------------------------------------------------
# General Transformation (fallback)
# ---------------------------------------------------------------------------

def _apply_general_transformation(task, matching_results, target_props):
    """
    일반 변환: example에서 input→output 직접 매핑을 추출하고 적용한다.
    color + position 동시 변환 등을 처리한다.
    """
    # color와 position 모두 변하는 경우
    if "color" in target_props and ("coordinate" in target_props or "position" in target_props):
        # position 변환 우선 시도 (색상은 보존)
        result = _apply_position_transformation(task, matching_results, target_props)
        if result is not None:
            return result

    # 각 target property별 개별 처리 시도
    for prop in target_props:
        if prop == "color":
            result = _apply_color_transformation(task, matching_results)
            if result is not None:
                return result
        elif prop in ("coordinate", "position"):
            result = _apply_position_transformation(task, matching_results, target_props)
            if result is not None:
                return result

    return None
