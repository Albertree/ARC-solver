"""
inspect.py — viz 함수 및 KG 저장 결과 확인 스크립트.

실행:
    python inspect.py

단계:
    [1] show_task       — 태스크 전체 시각화 (ANSI 색상)
    [2] show_objects    — 그리드별 object 목록 (5열 배치)
    [3] show_comparison — 두 컴포넌트 가로 비교 (Grid / Object / Pixel)
    [4] compare 결과    — Grid·Object 비교 score/COMM/DIFF 출력
    [5] 파일 트리       — semantic_memory/ 저장 구조 확인
    [6] 속성 파일 샘플  — 저장된 JSON 내용 확인
"""

import json
import os

from managers.arc_manager import ARCManager
from ARCKG import compare
from basics.viz import show_task, show_objects, show_comparison

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
SEMANTIC_MEMORY_ROOT = "semantic_memory"
TASK_ID = "08ed6ac7"          # ← 바꿔가며 테스트
COLORS = {0:".", 1:"B", 2:"R", 3:"G", 4:"Y", 5:"W", 6:"M", 7:"O", 8:"A", 9:"P"}


# ─────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────
def pause(msg="계속"):
    input(f"\n\033[33m[ Enter → {msg} ]\033[0m  ")


def walk_tree(root: str, max_files: int = 50):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel   = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        ind   = "  " * depth
        if rel != ".":
            print(f"{ind}📁 {os.path.basename(dirpath)}/")
        for fname in sorted(filenames):
            if count >= max_files:
                print(f"{ind}  ... (이하 생략)")
                return
            print(f"{ind}  📄 {fname}")
            count += 1


def show_json(path: str, skip_keys: tuple = ()):
    if not os.path.exists(path):
        print(f"  (파일 없음: {path})")
        return
    with open(path) as f:
        data = json.load(f)
    if skip_keys:
        data = {k: v for k, v in data.items() if k not in skip_keys}
        if "result" in data and isinstance(data["result"], dict):
            data["result"] = {
                k: v for k, v in data["result"].items() if k not in skip_keys
            }
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def main():
    mgr  = ARCManager(data_root="data", semantic_memory_root=SEMANTIC_MEMORY_ROOT)
    task = mgr.load_task(TASK_ID)
    print(f"\n로드 완료: {task}")

    # ═══════════════════════════════════════════════════════
    # [1] show_task — 태스크 전체 시각화
    # ═══════════════════════════════════════════════════════
    pause("show_task 실행")
    show_task(task)

    # ═══════════════════════════════════════════════════════
    # [2] show_objects — pair 0 input / output grid
    # ═══════════════════════════════════════════════════════
    pause("show_objects (Pair 0 input) 실행")
    show_objects(task.example_pairs[0].input_grid)

    pause("show_objects (Pair 0 output) 실행")
    if task.example_pairs[0].output_grid:
        show_objects(task.example_pairs[0].output_grid)

    # ═══════════════════════════════════════════════════════
    # [3] show_comparison — Grid / Object / Pixel
    # ═══════════════════════════════════════════════════════
    pause("show_comparison (Grid vs Grid) 실행")
    g0 = task.example_pairs[0].input_grid
    g1 = task.example_pairs[0].output_grid
    if g1:
        show_comparison(g0, g1)

    pause("show_comparison (Object vs Object) 실행")
    objs_in  = [o for o in g0.objects  if o.color != 0]
    objs_out = [o for o in g1.objects  if o.color != 0] if g1 else []
    if objs_in and objs_out:
        show_comparison(objs_in[0], objs_out[0])
        if len(objs_in) > 1 and len(objs_out) > 1:
            show_comparison(objs_in[1], objs_out[1])

    pause("show_comparison (Pixel vs Pixel) 실행")
    if objs_in and objs_in[0].pixels and objs_out and objs_out[0].pixels:
        show_comparison(objs_in[0].pixels[0], objs_out[0].pixels[0])

    # cross-pair Grid 비교
    if len(task.example_pairs) >= 2:
        pause("show_comparison (cross-pair Grid) 실행")
        g2 = task.example_pairs[1].input_grid
        show_comparison(g0, g2)

    # ═══════════════════════════════════════════════════════
    # [4] compare 결과 출력 (save=True → semantic_memory 기록)
    # ═══════════════════════════════════════════════════════
    pause("compare 결과 확인")

    print("\n── Grid compare (input vs output) ──")
    for i, pair in enumerate(task.example_pairs):
        if pair.output_grid is None:
            continue
        r = compare(pair.input_grid, pair.output_grid,
                    save=True, semantic_memory_root=SEMANTIC_MEMORY_ROOT)["result"]
        comm = [k for k, v in r["category"].items() if v["type"] == "COMM"]
        diff = [k for k, v in r["category"].items() if v["type"] == "DIFF"]
        print(f"  Pair{i}: {r['type']}  score={r['score']}")
        print(f"    COMM={comm}  DIFF={diff}")

    print("\n── Object compare (같은 색 쌍) ──")
    for i, pair in enumerate(task.example_pairs):
        if pair.output_grid is None:
            continue
        in_map  = {o.color: o for o in pair.input_grid.objects  if o.color != 0}
        out_map = {o.color: o for o in pair.output_grid.objects if o.color != 0}
        for c in sorted(set(in_map) & set(out_map)):
            r = compare(in_map[c], out_map[c],
                        save=True, semantic_memory_root=SEMANTIC_MEMORY_ROOT)["result"]
            diff = [k for k, v in r["category"].items() if v["type"] == "DIFF"]
            print(f"  Pair{i} color={COLORS.get(c,c)}({c}): "
                  f"score={r['score']}  DIFF={diff}")

    # ═══════════════════════════════════════════════════════
    # [5] semantic_memory 파일 트리
    # ═══════════════════════════════════════════════════════
    pause("파일 트리 확인")
    print(f"\nsemantic_memory/ (최대 50개):")
    walk_tree(SEMANTIC_MEMORY_ROOT, max_files=50)

    edge_files = []
    for root, _, files in os.walk(SEMANTIC_MEMORY_ROOT):
        for f in files:
            if f.startswith("E_") and "-" in f:
                edge_files.append(os.path.relpath(os.path.join(root, f),
                                                  SEMANTIC_MEMORY_ROOT))
    print(f"\n비교 엣지 파일: {len(edge_files)}개")
    for ef in sorted(edge_files):
        print(f"  {ef}")

    # ═══════════════════════════════════════════════════════
    # [6] 저장된 JSON 샘플 출력
    # ═══════════════════════════════════════════════════════
    pause("속성/엣지 파일 샘플 확인")
    task_dir = os.path.join(SEMANTIC_MEMORY_ROOT, f"N_T{TASK_ID}")

    print(f"\n── E_T{TASK_ID}.json (TASK 속성):")
    show_json(os.path.join(task_dir, f"E_T{TASK_ID}.json"))

    print(f"\n── N_P0/E_P0.json (PAIR 속성):")
    show_json(os.path.join(task_dir, "N_P0", "E_P0.json"))

    print(f"\n── N_P0/N_G0/E_G0.json (GRID 속성, contents 생략):")
    show_json(os.path.join(task_dir, "N_P0", "N_G0", "E_G0.json"),
              skip_keys=("contents",))

    # Object 샘플
    g0_dir = os.path.join(task_dir, "N_P0", "N_G0")
    obj_dirs = sorted(d for d in os.listdir(g0_dir) if d.startswith("N_O"))
    if obj_dirs:
        o_name = obj_dirs[0]
        o_id   = o_name[2:]
        print(f"\n── N_P0/N_G0/{o_name}/E_{o_id}.json (OBJECT 속성):")
        show_json(os.path.join(g0_dir, o_name, f"E_{o_id}.json"),
                  skip_keys=("coordinate", "shape"))

    # Edge 샘플
    if edge_files:
        sample = sorted(edge_files)[0]
        print(f"\n── 비교 엣지 샘플: {sample}")
        show_json(os.path.join(SEMANTIC_MEMORY_ROOT, sample),
                  skip_keys=("category",))

    print("\n\033[32m완료.\033[0m")


if __name__ == "__main__":
    main()
