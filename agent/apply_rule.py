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

    접근법:
    1. example matched pair에서 object별 변환 패턴 추출
    2. 변환의 ordering criterion 발견 (어떤 property 기준으로 정렬 → 어떤 값 부여)
    3. test input object에 동일 패턴 적용
    4. output grid 생성
    """
    matching_results = wm.get("matching-results") or {}
    transform_targets = wm.get("transform-targets") or []

    if not transform_targets:
        return None

    target_prop = transform_targets[0]["property"] if transform_targets else None
    if target_prop != "color":
        # 현재는 color 변환만 지원
        return None

    # 1. example pair에서 변환 패턴 추출
    example_patterns = _extract_example_patterns(task, matching_results)
    if not example_patterns:
        return None

    # 2. ordering criterion 발견
    ordering_criterion, color_sequence = _discover_ordering(example_patterns)
    if ordering_criterion is None:
        return None

    # 3. test input에 적용
    for test_pair in task.test_pairs:
        test_grid = test_pair.input_grid
        predicted = _apply_to_test(test_grid, ordering_criterion, color_sequence)
        if predicted is not None:
            return predicted

    return None


def _extract_example_patterns(task, matching_results: dict) -> list[list[dict]]:
    """
    각 example pair에서 matched object의 변환 데이터를 추출한다.

    반환: [
        [  # pair 0
            {"input_area": 9, "input_color": 5, "output_color": 1, "coordinate": [...]},
            ...
        ],
        ...
    ]
    """
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

            # color가 실제로 변한 쌍만 추출
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


def _discover_ordering(example_patterns: list[list[dict]]) -> tuple:
    """
    example pattern에서 ordering criterion을 발견한다.

    여러 property(area, height, pos_row, pos_col)로 정렬해보고,
    모든 example에서 일관된 color sequence를 산출하는 criterion을 선택한다.

    반환: (criterion_key, color_sequence)
        criterion_key: "input_area" | "input_height" | "input_pos_col" | ...
        color_sequence: [1, 2, 3, 4] 등 — 정렬 후 부여할 색상 순서
    """
    # 시도할 ordering 기준 (descending)
    criteria = [
        ("input_area", True),      # 면적 내림차순
        ("input_height", True),    # 높이 내림차순
        ("input_pos_col", False),  # 열 위치 오름차순
        ("input_pos_row", False),  # 행 위치 오름차순
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

    # 어떤 criterion도 일관되지 않으면, 첫 example의 area 기준 사용
    if example_patterns:
        pair_data = example_patterns[0]
        sorted_data = sorted(pair_data, key=lambda x: x["input_area"], reverse=True)
        sequence = [d["output_color"] for d in sorted_data]
        return "input_area", sequence

    return None, None


def _apply_to_test(
    test_grid,
    ordering_criterion: str,
    color_sequence: list[int],
) -> list[list[int]] | None:
    """
    test input grid에 학습된 변환을 적용하여 output grid를 생성한다.
    """
    test_objects = test_grid.objects
    if not test_objects:
        return None

    # 변환 대상 object만 필터 (배경이 아닌 object)
    # 배경색(0)이 아닌 object만 변환 대상
    target_objects = []
    for obj in test_objects:
        if obj.color != 0:
            target_objects.append(obj)

    if not target_objects:
        return None

    # ordering criterion에 따라 정렬
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

    # 색상 부여: color_sequence에서 순서대로
    output = copy.deepcopy(test_grid.raw)
    for rank, obj in enumerate(sorted_objects):
        if rank < len(color_sequence):
            new_color = color_sequence[rank]
        else:
            new_color = rank + 1  # fallback

        for r, c in obj.coordinate:
            if 0 <= r < len(output) and 0 <= c < len(output[0]):
                output[r][c] = new_color

    return output
