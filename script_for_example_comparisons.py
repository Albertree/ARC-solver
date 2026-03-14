#!/usr/bin/env python3
"""
Generate example comparison JSONs (0th–3rd order) under example_comparisons/.

Edit the CONFIG section below to choose:
- TASK_HEX_CODE: which ARC task to load
- COMPONENT_LEVEL: "grid" | "object" | "pixel" (pool to draw from)

The script builds a pool of all components at that level (e.g. all grids from
all example pairs), then randomly samples (with replacement allowed) to produce:
- 0th/: 8 property files (E_{short}_n.json, n=0..7; _n avoids overwrite when same node is picked again)
- 1st/: 4 node-vs-node comparison files
- 2nd/: 2 edge-vs-edge comparison files (from pairs of 1st-order results)
- 3rd/: 1 file (comparison of the 2 second-order results)
"""

import os
import json
import sys
import random

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------
TASK_HEX_CODE = "08ed6ac7"
COMPONENT_LEVEL = "object"   # "grid" | "object" | "pixel"
OUT_DIR = "example_comparisons8"   # e.g. example_comparisons7 for 4 objects, level 2 only

# Restrict pool: None = all; RESTRICT_TO_PAIR = int = that pair only; RESTRICT_TO_GRID = (pair_idx, grid_idx) = that grid only (grid_idx 0=input, 1=output).
RESTRICT_TO_PAIR = None
RESTRICT_TO_GRID = None

# When set (e.g. [0,1,...,7]), pool = only these pixel indices from the single grid. Requires RESTRICT_TO_GRID and COMPONENT_LEVEL="pixel".
FIXED_PIXEL_INDICES = None

# When set, pool = pixels from each (grid, indices). Each item: ((pair_idx, grid_idx), [indices]).
FIXED_PIXEL_BY_GRID = None

# When set, pool = objects from each (grid, indices). Each item: ((pair_idx, grid_idx), [object_indices]).
FIXED_OBJECT_BY_GRID = None

# When set, pool = exactly these objects. Each item: (pair_idx, grid_idx, object_idx). P0G0O0, P0G1O0, P1G0O0, P1G1O0 → 1st pairs (0,1),(2,3); 2nd = 1.
FIXED_OBJECTS_LIST = [
    (0, 0, 1),   # Pair 0 GRID 0 Object 0
    (0, 1, 2),   # Pair 0 GRID 1 Object 0
    (1, 0, 0),   # Pair 1 GRID 0 Object 0
    (1, 1, 1),   # Pair 1 GRID 1 Object 0
]

# Max comparison order to generate (2 = 0th + 1st + 2nd only; 3 = include 3rd).
MAX_ORDER = 2

# Counts per order (used when generating; for FIXED_OBJECTS_LIST with 4 items we use N_1ST=2, N_2ND=1)
N_0TH = 8
N_1ST = 2
N_2ND = 1
N_3RD = 1
# -----------------------------------------------------------------------------


def collect_pool(task, level, restrict_to_pair=None, restrict_to_grid=None, fixed_pixel_indices=None, fixed_pixel_by_grid=None, fixed_object_by_grid=None, fixed_objects_list=None):
    """Collect components. fixed_objects_list = [(pair_idx, grid_idx, object_idx), ...] for exact object list."""
    pool = []
    pairs = task.example_pairs
    if fixed_objects_list is not None and level == "object":
        for (pi, gi, oi) in fixed_objects_list:
            if pi < 0 or pi >= len(pairs):
                continue
            grid = (pairs[pi].input_grid, pairs[pi].output_grid)[gi]
            objects = getattr(grid, "objects", [])
            if 0 <= oi < len(objects):
                pool.append(objects[oi])
        return pool
    if fixed_pixel_by_grid is not None and level == "pixel":
        for (pi, gi), indices in fixed_pixel_by_grid:
            if pi < 0 or pi >= len(pairs):
                continue
            grid = (pairs[pi].input_grid, pairs[pi].output_grid)[gi]
            pixels = getattr(grid, "pixels", [])
            for i in indices:
                if 0 <= i < len(pixels):
                    pool.append(pixels[i])
        return pool
    if fixed_object_by_grid is not None and level == "object":
        for (pi, gi), indices in fixed_object_by_grid:
            if pi < 0 or pi >= len(pairs):
                continue
            grid = (pairs[pi].input_grid, pairs[pi].output_grid)[gi]
            objects = getattr(grid, "objects", [])
            for i in indices:
                if 0 <= i < len(objects):
                    pool.append(objects[i])
        return pool
    if restrict_to_grid is not None:
        pi, gi = restrict_to_grid
        if pi < 0 or pi >= len(pairs):
            return pool
        grid = (pairs[pi].input_grid, pairs[pi].output_grid)[gi]
        grids = [grid]
    elif restrict_to_pair is not None:
        if restrict_to_pair < 0 or restrict_to_pair >= len(pairs):
            return pool
        grids = [pairs[restrict_to_pair].input_grid, pairs[restrict_to_pair].output_grid]
    else:
        grids = []
        for pair in pairs:
            grids.extend([pair.input_grid, pair.output_grid])
    for grid in grids:
        if level == "grid":
            pool.append(grid)
        elif level == "object":
            for obj in getattr(grid, "objects", []):
                pool.append(obj)
        elif level == "pixel":
            pixels = getattr(grid, "pixels", [])
            if fixed_pixel_indices is not None and restrict_to_grid is not None and len(grids) == 1:
                for i in fixed_pixel_indices:
                    if 0 <= i < len(pixels):
                        pool.append(pixels[i])
            else:
                for px in pixels:
                    pool.append(px)
    return pool


def main():
    from managers.arc_manager import ARCManager
    from ARCKG.comparison import (
        compare,
        get_component_full_id,
        id_to_json_path,
        node_id_to_short_name,
        load_json_file,
    )

    for sub in ("0th", "1st", "2nd", "3rd"):
        os.makedirs(os.path.join(OUT_DIR, sub), exist_ok=True)
    print(f"Loading task {TASK_HEX_CODE}...")
    task = ARCManager.from_hex_code(TASK_HEX_CODE)
    pool = collect_pool(task, COMPONENT_LEVEL, RESTRICT_TO_PAIR, RESTRICT_TO_GRID, FIXED_PIXEL_INDICES, FIXED_PIXEL_BY_GRID, FIXED_OBJECT_BY_GRID, FIXED_OBJECTS_LIST)
    if not pool:
        print(f"No components found at level {COMPONENT_LEVEL}.")
        sys.exit(1)
    print(f"Pool size at {COMPONENT_LEVEL}: {len(pool)}")

    use_fixed = (
        (FIXED_PIXEL_INDICES is not None and COMPONENT_LEVEL == "pixel" and RESTRICT_TO_GRID is not None)
        or (FIXED_PIXEL_BY_GRID is not None and COMPONENT_LEVEL == "pixel")
        or (FIXED_OBJECT_BY_GRID is not None and COMPONENT_LEVEL == "object")
        or (FIXED_OBJECTS_LIST is not None and COMPONENT_LEVEL == "object")
    )
    if use_fixed:
        random.seed(42)  # still used for any tie-break; 1st pairs are fixed below

    def save_json(data, filename, subdir):
        path = os.path.join(OUT_DIR, subdir, filename)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  saved: {path}")

    # 0th order
    print("0th order (property)...")
    n_0th = len(pool) if use_fixed else N_0TH
    for i in range(n_0th):
        if use_fixed and i >= len(pool):
            continue
        comp = pool[i] if use_fixed else random.choice(pool)
        node_id = get_component_full_id(comp)
        try:
            prop_path = id_to_json_path(node_id)
            prop = load_json_file(prop_path)
        except FileNotFoundError:
            prop = getattr(comp, "property", None) or {}
        short = node_id_to_short_name(node_id) or "node"
        if use_fixed:
            save_json(prop, f"E_{short}.json", "0th")
        else:
            save_json(prop, f"E_{short}_{i}.json", "0th")

    # 1st order: 4 node-vs-node (fixed pairs when use_fixed: (0,4),(1,5),(2,6),(3,7) for grid0 Xi vs grid1 Xi if pool is 8 from two grids; else (0,1),(2,3),(4,5),(6,7))
    print("1st order (node vs node)...")
    first_results = []
    if use_fixed and len(pool) == 4 and FIXED_OBJECTS_LIST is not None:
        # P0G0O0 vs P0G1O0, P1G0O0 vs P1G1O0
        pairs_1st = [(0, 1), (2, 3)]
    elif use_fixed and len(pool) == 8 and (
        (FIXED_PIXEL_BY_GRID is not None and len(FIXED_PIXEL_BY_GRID) == 2)
        or (FIXED_OBJECT_BY_GRID is not None and len(FIXED_OBJECT_BY_GRID) == 2)
    ):
        # grid0 indices 0..3 vs grid1 indices 0..3 (pool 4+4): pair (0,4), (1,5), (2,6), (3,7)
        pairs_1st = [(0, 4), (1, 5), (2, 6), (3, 7)]
    elif use_fixed and len(pool) >= 8:
        pairs_1st = [(0, 1), (2, 3), (4, 5), (6, 7)]
    else:
        pairs_1st = None
    for i in range(N_1ST):
        if pairs_1st is not None and i < len(pairs_1st):
            a, b = pool[pairs_1st[i][0]], pool[pairs_1st[i][1]]
        elif len(pool) >= 2:
            a, b = random.sample(pool, 2)
        else:
            a = b = pool[0]
        res = compare(a, b, save=False)
        first_results.append(res)
        save_json(res, f"{res['edge_id']}.json", "1st")

    # 2nd order: edge-vs-edge (pair 1st results)
    if MAX_ORDER >= 2 and len(first_results) >= N_2ND * 2:
        print("2nd order (edge vs edge)...")
        second_results = []
        for j in range(N_2ND):
            i1, i2 = j * 2, j * 2 + 1
            if i2 > len(first_results):
                break
            r1, r2 = first_results[i1], first_results[i2]
            res = compare(
                r1["result"],
                r2["result"],
                save=False,
                edge_id1=r1["edge_id"],
                edge_id2=r2["edge_id"],
                task_hex=TASK_HEX_CODE,
            )
            second_results.append(res)
            save_json(res, f"{res['edge_id']}.json", "2nd")

        # 3rd order: 1 file (only if MAX_ORDER >= 3)
        if MAX_ORDER >= 3 and len(second_results) >= 2:
            print("3rd order...")
            r1, r2 = second_results[0], second_results[1]
            third = compare(
                r1["result"],
                r2["result"],
                save=False,
                edge_id1=r1["edge_id"],
                edge_id2=r2["edge_id"],
                task_hex=TASK_HEX_CODE,
            )
            save_json(third, f"{third['edge_id']}.json", "3rd")

    print("Done.")


if __name__ == "__main__":
    main()
