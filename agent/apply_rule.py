"""
apply_rule — DIFF→DSL 파이프라인.

compare() 결과에서 DIFF property를 감지하고, comp1/comp2 실제 값으로부터
DSL 인자를 계산하여 coloring/make_grid 시퀀스를 생성한다.

모든 transformation은 coloring(selection, color)과 make_grid(h, w, color)의
조합으로 표현된다. 다른 transformation 함수를 추가하지 않는다.
"""

from __future__ import annotations

import copy
from dsl.primitives import coloring, make_grid


def apply_learned_rule(task, wm) -> list[list[int]] | None:
    """
    example pair의 compare 결과에서 DIFF→DSL 시퀀스를 생성하고
    test input에 적용하여 predicted output grid를 반환한다.
    """
    # DSL 적용에는 항상 lenient matching 사용 (threshold 없이 greedy)
    # Phase 1의 5/8 threshold는 분석용이며, 실제 변환 적용에서는
    # 색상+위치 동시 변환(score=5/8) 등을 놓치지 않도록 한다
    matching_results = _build_matching_from_examples(task)
    compare_results = wm.get("compare-results") or _build_compare_from_examples(task)

    # example pair에서 DSL 시퀀스 추출
    dsl_sequences = _extract_dsl_sequences(task, matching_results, compare_results)
    if not dsl_sequences:
        return None

    # test input에 적용
    results = []
    for test_pair in task.test_pairs:
        predicted = _apply_dsl_to_test(
            test_pair.input_grid, dsl_sequences, task, matching_results, compare_results
        )
        results.append(predicted)

    # 첫 번째 test만 반환 (multi-test는 향후 확장)
    return results[0] if results else None


# ---------------------------------------------------------------------------
# DIFF → DSL 시퀀스 추출
# ---------------------------------------------------------------------------

def _extract_dsl_sequences(task, matching_results, compare_results) -> list[dict]:
    """
    각 example pair의 matched object별 DIFF property에서 DSL 시퀀스를 생성한다.

    반환: [
        {
            "pair_id": "T...P0",
            "object_sequences": [
                {"match": {...}, "dsl_steps": [{"fn": "coloring", "selection": ..., "color": ...}, ...]}
            ]
        }
    ]
    """
    # compare_results를 (id1, id2) → result 인덱스
    obj_results = {}
    for entry in compare_results:
        if entry.get("level") == "OBJECT":
            key = (entry["id1"], entry["id2"])
            obj_results[key] = entry["result"]

    all_sequences = []
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue

        pair_matching = matching_results.get(pair.node_id, {})
        matched = pair_matching.get("matched", [])
        input_objs = {o.node_id: o for o in pair.input_grid.objects}
        output_objs = {o.node_id: o for o in pair.output_grid.objects}

        obj_seqs = []
        for match in matched:
            in_obj = input_objs.get(match["id1"])
            out_obj = output_objs.get(match["id2"])
            if not in_obj or not out_obj:
                continue

            # 배경 object(color 0) 쌍은 건너뛴다
            if in_obj.color == 0 and out_obj.color == 0:
                continue

            # compare 결과에서 DIFF category 추출
            result_key = (match["id1"], match["id2"])
            cmp_result = obj_results.get(result_key)

            dsl_steps = _diff_to_dsl(in_obj, out_obj, cmp_result)
            if dsl_steps:
                obj_seqs.append({"match": match, "dsl_steps": dsl_steps})

        if obj_seqs:
            all_sequences.append({
                "pair_id": pair.node_id,
                "object_sequences": obj_seqs,
            })

    return all_sequences


def _diff_to_dsl(in_obj, out_obj, cmp_result) -> list[dict]:
    """
    한 쌍의 matched object에서 DIFF property를 감지하고
    comp1/comp2 값으로부터 DSL 시퀀스를 생성한다.
    """
    dsl_steps = []

    if cmp_result is None:
        # compare 결과 없으면 직접 비교
        cmp_result = _quick_compare(in_obj, out_obj)

    cat = cmp_result.get("result", {}).get("category", {})

    # --- color DIFF → coloring(coords, comp2_color) ---
    color_cat = cat.get("color", {})
    if color_cat.get("type") == "DIFF":
        out_coords = [[r, c] for r, c in out_obj.coordinate]
        out_color = out_obj.color
        dsl_steps.append({
            "fn": "coloring",
            "selection": out_coords,
            "color": out_color,
            "diff_property": "color",
            "comp1": in_obj.color,
            "comp2": out_color,
        })

    # --- coordinate DIFF → coloring(old, 13) + coloring(new, color) ---
    coord_cat = cat.get("coordinate", {})
    if coord_cat.get("type") == "DIFF":
        comp1_coords = coord_cat.get("comp1", [[r, c] for r, c in in_obj.coordinate])
        comp2_coords = coord_cat.get("comp2", [[r, c] for r, c in out_obj.coordinate])
        obj_color = out_obj.color

        # 이전 위치 지우기 (투명)
        dsl_steps.append({
            "fn": "coloring",
            "selection": comp1_coords,
            "color": 13,
            "diff_property": "coordinate",
            "action": "erase_old",
        })
        # 새 위치에 칠하기
        dsl_steps.append({
            "fn": "coloring",
            "selection": comp2_coords,
            "color": obj_color,
            "diff_property": "coordinate",
            "action": "paint_new",
        })

    # --- size DIFF → make_grid + coloring ---
    size_cat = cat.get("size", {})
    if size_cat.get("type") == "DIFF":
        size_detail = size_cat.get("category", {})
        comp2_h = size_detail.get("height", {}).get("comp2", out_obj.pos[0])
        comp2_w = size_detail.get("width", {}).get("comp2", out_obj.pos[1])
        if isinstance(comp2_h, int) and isinstance(comp2_w, int):
            dsl_steps.append({
                "fn": "make_grid",
                "height": comp2_h,
                "width": comp2_w,
                "color": 0,
                "diff_property": "size",
            })
            # 새 크기 grid에 object 색칠
            out_coords = [[r, c] for r, c in out_obj.coordinate]
            dsl_steps.append({
                "fn": "coloring",
                "selection": out_coords,
                "color": out_obj.color,
                "diff_property": "size",
                "action": "repaint",
            })

    return dsl_steps


# ---------------------------------------------------------------------------
# Test input에 DSL 적용
# ---------------------------------------------------------------------------

def _apply_dsl_to_test(test_grid, dsl_sequences, task, matching_results, compare_results):
    """
    example에서 추출한 DSL 시퀀스를 test input에 적용한다.

    핵심: example DSL에서 delta/패턴을 추출하고, test object에 동일 delta를 적용한다.
    """
    test_objs = [o for o in test_grid.objects if o.color != 0]
    if not test_objs:
        return None

    # example에서 공통 변환 패턴(delta) 추출
    transform_info = _extract_transform_pattern(dsl_sequences, task)
    if not transform_info:
        return None

    grid = copy.deepcopy(test_grid.raw)

    # color ordering: 여러 object에 순서대로 다른 색 부여하는 패턴
    if transform_info["type"] == "color_ordering":
        return _apply_color_ordering_dsl(grid, test_objs, dsl_sequences, task, matching_results)

    for obj in test_objs:
        grid = _apply_transform_to_object(grid, obj, transform_info, test_grid)

    return grid


def _extract_transform_pattern(dsl_sequences, task):
    """
    example DSL 시퀀스에서 공통 변환 패턴을 추출한다.
    comp1/comp2 실제 값으로부터 delta, target_pos 등을 계산한다.
    """
    if not dsl_sequences:
        return None

    # 모든 example의 모든 object DSL step을 수집
    all_color_diffs = []
    all_coord_diffs = []

    input_objs_map = {}
    output_objs_map = {}
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        for o in pair.input_grid.objects:
            input_objs_map[o.node_id] = o
        for o in pair.output_grid.objects:
            output_objs_map[o.node_id] = o

    for seq in dsl_sequences:
        for obj_seq in seq["object_sequences"]:
            match = obj_seq["match"]
            in_obj = input_objs_map.get(match["id1"])
            out_obj = output_objs_map.get(match["id2"])
            if not in_obj or not out_obj:
                continue

            # 배경 object는 건너뛴다
            if in_obj and in_obj.color == 0 and out_obj and out_obj.color == 0:
                continue

            for step in obj_seq["dsl_steps"]:
                if step.get("diff_property") == "color" and "comp1" in step and "comp2" in step:
                    # 배경색(0) 관련 변환은 무시
                    if step["comp1"] != 0 or step["comp2"] != 0:
                        all_color_diffs.append({
                            "comp1": step["comp1"],
                            "comp2": step["comp2"],
                        })
                elif step.get("diff_property") == "coordinate":
                    if step.get("action") == "paint_new":
                        in_coords = sorted(in_obj.coordinate)
                        out_coords = sorted(out_obj.coordinate)
                        if in_coords and out_coords:
                            dr = out_coords[0][0] - in_coords[0][0]
                            dc = out_coords[0][1] - in_coords[0][1]
                            all_coord_diffs.append({
                                "delta": (dr, dc),
                                "grid_h": None,
                                "grid_w": None,
                                "in_obj": in_obj,
                                "out_obj": out_obj,
                            })

    result = {"type": "unknown", "steps": []}

    # color 변환만 있는 경우
    if all_color_diffs and not all_coord_diffs:
        # 여러 object가 각각 다른 comp2를 가지면 → color ordering
        comp2_values = set(cd["comp2"] for cd in all_color_diffs)
        if len(comp2_values) > 1:
            result["type"] = "color_ordering"
            result["color_diffs"] = all_color_diffs
            return result
        # 모두 같은 comp2 → 단순 color 변환
        result["type"] = "color_only"
        result["color_diffs"] = all_color_diffs
        return result

    # coordinate 변환이 있는 경우
    if all_coord_diffs:
        deltas = [d["delta"] for d in all_coord_diffs]

        # 모든 delta가 동일한지 확인 (relative move)
        if len(set(deltas)) == 1:
            result["type"] = "relative_move"
            result["delta"] = deltas[0]
            result["color_diffs"] = all_color_diffs
            return result

        # anchor 패턴 확인: output이 grid 경계 정렬인지
        anchor = _detect_anchor(all_coord_diffs, task)
        if anchor:
            result["type"] = "anchor_move"
            result["anchor"] = anchor
            result["color_diffs"] = all_color_diffs
            return result

        # 대각선 슬라이딩 패턴 확인: delta = min(dist_to_bottom, dist_to_right)
        slide = _detect_diagonal_slide(all_coord_diffs, task)
        if slide:
            result["type"] = "diagonal_slide"
            result["slide_direction"] = slide
            result["color_diffs"] = all_color_diffs
            return result

        # fallback: 첫 example의 delta 사용
        result["type"] = "relative_move"
        result["delta"] = deltas[0]
        result["color_diffs"] = all_color_diffs
        return result

    # color ordering 패턴 (08ed6ac7 유형)
    if all_color_diffs:
        result["type"] = "color_ordering"
        result["color_diffs"] = all_color_diffs
        return result

    return None


def _detect_diagonal_slide(coord_diffs, task):
    """
    대각선 슬라이딩 패턴 감지: 각 object가 대각선으로 이동하되
    delta = min(edge까지 거리들)로 결정되는 패턴.
    예: (1,4) in 6x6 → min(5-1, 5-4) = 1 → delta=(1,1) → (2,5)
    """
    gh, gw = None, None
    for pair in task.example_pairs:
        if pair.output_grid is not None:
            gh = pair.output_grid.height
            gw = pair.output_grid.width
            break
    if gh is None:
        return None

    # (dr_sign, dc_sign) 방향을 추론: 가장 빈번한 방향
    directions = [(+1, +1), (+1, -1), (-1, +1), (-1, -1)]
    for dr_sign, dc_sign in directions:
        all_match = True
        for d in coord_diffs:
            in_obj = d["in_obj"]
            out_obj = d["out_obj"]
            ir, ic = in_obj.pos[0], in_obj.pos[1]
            oh = len(in_obj.colorgrid)
            ow = len(in_obj.colorgrid[0]) if in_obj.colorgrid else 0

            # 각 방향에서 edge까지 거리 계산
            if dr_sign > 0:
                dist_r = (gh - oh) - ir
            else:
                dist_r = ir
            if dc_sign > 0:
                dist_c = (gw - ow) - ic
            else:
                dist_c = ic

            expected_delta = min(dist_r, dist_c)
            expected_pos = (ir + dr_sign * expected_delta, ic + dc_sign * expected_delta)

            if out_obj.pos != expected_pos:
                all_match = False
                break

        if all_match:
            return {"dr_sign": dr_sign, "dc_sign": dc_sign}

    return None


def _detect_anchor(coord_diffs, task):
    """output 좌표가 grid 코너에 정렬되는지 확인."""
    gh, gw = None, None
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        gh = pair.output_grid.height
        gw = pair.output_grid.width
        break
    if gh is None:
        return None

    # 각 코너 확인
    anchors = {
        "bottom_right": lambda obj: obj.pos == (gh - len(obj.colorgrid), gw - (len(obj.colorgrid[0]) if obj.colorgrid else 0)),
        "top_left": lambda obj: obj.pos == (0, 0),
        "top_right": lambda obj: obj.pos == (0, gw - (len(obj.colorgrid[0]) if obj.colorgrid else 0)),
        "bottom_left": lambda obj: obj.pos == (gh - len(obj.colorgrid), 0),
    }

    for anchor_name, check_fn in anchors.items():
        if all(check_fn(d["out_obj"]) for d in coord_diffs):
            return anchor_name

    return None


def _apply_transform_to_object(grid, obj, transform_info, test_grid):
    """단일 test object에 변환 패턴을 적용."""
    ttype = transform_info["type"]
    gh = len(grid)
    gw = len(grid[0]) if gh > 0 else 0

    if ttype == "color_only":
        color_diffs = transform_info.get("color_diffs", [])
        new_color = _resolve_color(obj.color, color_diffs)
        grid = coloring(grid, [[r, c] for r, c in obj.coordinate], new_color)

    elif ttype == "color_ordering":
        # 여러 object 색상 순서 변경은 상위에서 처리 (단일 object 적용 아님)
        pass

    elif ttype == "relative_move":
        dr, dc = transform_info["delta"]
        old_coords = [[r, c] for r, c in obj.coordinate]
        new_coords = [[r + dr, c + dc] for r, c in obj.coordinate]
        # 색상 변환 확인
        color_diffs = transform_info.get("color_diffs", [])
        new_color = _resolve_color(obj.color, color_diffs)
        grid = coloring(grid, old_coords, 13)
        grid = coloring(grid, new_coords, new_color)

    elif ttype == "anchor_move":
        anchor = transform_info["anchor"]
        oh = len(obj.colorgrid)
        ow = len(obj.colorgrid[0]) if obj.colorgrid else 0
        if anchor == "bottom_right":
            new_r, new_c = gh - oh, gw - ow
        elif anchor == "top_left":
            new_r, new_c = 0, 0
        elif anchor == "top_right":
            new_r, new_c = 0, gw - ow
        elif anchor == "bottom_left":
            new_r, new_c = gh - oh, 0
        else:
            return grid

        old_coords = [[r, c] for r, c in obj.coordinate]
        base_r, base_c = obj.pos
        new_coords = [[r - base_r + new_r, c - base_c + new_c] for r, c in obj.coordinate]
        color_diffs = transform_info.get("color_diffs", [])
        new_color = _resolve_color(obj.color, color_diffs)
        grid = coloring(grid, old_coords, 13)
        grid = coloring(grid, new_coords, new_color)

    elif ttype == "diagonal_slide":
        slide = transform_info["slide_direction"]
        dr_sign = slide["dr_sign"]
        dc_sign = slide["dc_sign"]
        ir, ic = obj.pos
        oh = len(obj.colorgrid)
        ow = len(obj.colorgrid[0]) if obj.colorgrid else 0
        dist_r = ((gh - oh) - ir) if dr_sign > 0 else ir
        dist_c = ((gw - ow) - ic) if dc_sign > 0 else ic
        delta = min(dist_r, dist_c)
        old_coords = [[r, c] for r, c in obj.coordinate]
        new_coords = [[r + dr_sign * delta, c + dc_sign * delta] for r, c in obj.coordinate]
        color_diffs = transform_info.get("color_diffs", [])
        new_color = _resolve_color(obj.color, color_diffs)
        grid = coloring(grid, old_coords, 13)
        grid = coloring(grid, new_coords, new_color)

    return grid


def _resolve_color(input_color: int, color_diffs: list) -> int:
    """
    color_diffs에서 input_color에 대응하는 출력 색상을 결정한다.
    1. 직접 매핑 (comp1→comp2) 존재하면 사용
    2. 모든 comp2가 동일하면 constant output color 사용
    3. 없으면 input_color 유지
    """
    if not color_diffs:
        return input_color

    # 직접 매핑
    color_map = {cd["comp1"]: cd["comp2"] for cd in color_diffs}
    if input_color in color_map:
        return color_map[input_color]

    # constant output color: 모든 comp2가 동일
    comp2_values = set(cd["comp2"] for cd in color_diffs)
    if len(comp2_values) == 1:
        return comp2_values.pop()

    return input_color


# ---------------------------------------------------------------------------
# Color ordering (08ed6ac7 유형) — DSL 기반 재구현
# ---------------------------------------------------------------------------

def _apply_color_ordering_dsl(grid, test_objects, dsl_sequences, task, matching_results):
    """
    여러 object의 색상을 ordering 기반으로 변환.
    compare 결과의 comp1/comp2에서 색상 매핑을 추출.
    """
    input_objs_map = {}
    output_objs_map = {}
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        for o in pair.input_grid.objects:
            input_objs_map[o.node_id] = o
        for o in pair.output_grid.objects:
            output_objs_map[o.node_id] = o

    # example에서 area→output_color 매핑 추출
    area_color_maps = []
    for seq in dsl_sequences:
        area_map = {}
        for obj_seq in seq["object_sequences"]:
            match = obj_seq["match"]
            in_obj = input_objs_map.get(match["id1"])
            out_obj = output_objs_map.get(match["id2"])
            if in_obj and out_obj and in_obj.color != out_obj.color:
                area_map[len(in_obj.coordinate)] = out_obj.color
        if area_map:
            area_color_maps.append(area_map)

    if not area_color_maps:
        return grid

    # area 내림차순으로 test objects 정렬
    sorted_test = sorted(test_objects, key=lambda o: len(o.coordinate), reverse=True)

    # 첫 example의 area→color를 참조하여 순서별 색상 결정
    ref_map = area_color_maps[0]
    ref_sorted = sorted(ref_map.keys(), reverse=True)
    color_sequence = [ref_map[a] for a in ref_sorted]

    for rank, obj in enumerate(sorted_test):
        new_color = color_sequence[rank] if rank < len(color_sequence) else rank + 1
        grid = coloring(grid, [[r, c] for r, c in obj.coordinate], new_color)

    return grid


# ---------------------------------------------------------------------------
# Matching/Compare fallback (규칙만 로드된 경우)
# ---------------------------------------------------------------------------

def _build_matching_from_examples(task) -> dict:
    """example pair에서 직접 object matching을 수행한다."""
    from ARCKG.comparison import compare as kg_compare

    matching_results = {}
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue
        input_objs = pair.input_grid.objects
        output_objs = pair.output_grid.objects

        scored = []
        for io in input_objs:
            for oo in output_objs:
                result = kg_compare(io, oo)
                res = result.get("result", {})
                score_str = res.get("score", "0/0")
                parts = score_str.split("/")
                try:
                    num, denom = int(parts[0]), int(parts[1])
                except (ValueError, IndexError):
                    num, denom = 0, 0
                scored.append({
                    "id1": io.node_id, "id2": oo.node_id,
                    "score": score_str, "ratio": num / denom if denom > 0 else 0,
                })

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


def _build_compare_from_examples(task) -> list:
    """example pair에서 직접 compare 결과를 생성한다."""
    from ARCKG.comparison import compare as kg_compare

    results = []
    for pair in task.example_pairs:
        if pair.output_grid is None:
            continue

        # Grid level
        grid_result = kg_compare(pair.input_grid, pair.output_grid, save=True, semantic_memory_root="semantic_memory")
        results.append({"pair_id": pair.node_id, "id1": pair.input_grid.node_id, "id2": pair.output_grid.node_id, "level": "GRID", "result": grid_result})

        # Object level
        for io in pair.input_grid.objects:
            for oo in pair.output_grid.objects:
                obj_result = kg_compare(io, oo, save=True, semantic_memory_root="semantic_memory")
                results.append({"pair_id": pair.node_id, "id1": io.node_id, "id2": oo.node_id, "level": "OBJECT", "result": obj_result})

    return results


def _quick_compare(in_obj, out_obj):
    """compare 결과가 없을 때 빠른 비교."""
    from ARCKG.comparison import compare as kg_compare
    return kg_compare(in_obj, out_obj)
