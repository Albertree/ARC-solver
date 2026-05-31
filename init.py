"""
ARC-solver 메모리/로그 초기화.

*생성된* 메모리·로그를 비우되, **초기 제공 seed 는 보존**한다.
  · semantic_memory   — 생성물 (ARCKG 노드 dump + dsl_library.json[학습]) → 비움
  · episodic_memory    — 생성물 (풀이 trace) → 비움
  · procedural_memory  — **seed DSL 코드(DSL/, __init__.py)는 보존** (메모리 아님)
  · run_logs           — 로그 → 비움
  · eval_result        — eval 격리 런 결과 → 비움

--confirm 없으면 dry-run (목록만). data/ 는 read-only seed 이므로 대상 아님.

사용법:
  python init.py               dry-run
  python init.py --confirm     실제 초기화
  python init.py --roots semantic_memory run_logs --confirm   일부만
"""

import argparse
import shutil
from pathlib import Path

# root → 보존할 top-level 이름 (이외 항목 삭제). ".gitkeep" 은 항상 보존.
PRESERVE = {
    "procedural_memory": {"DSL", "__init__.py"},   # seed DSL 코드 — 절대 삭제 금지
}

DEFAULT_ROOTS = [
    "semantic_memory",
    "episodic_memory",
    "procedural_memory",
    "run_logs",
    "eval_result",
]


def _init_dir(root: str, dry_run: bool, preserve: set) -> int:
    """root/ 아래에서 (preserve ∪ .gitkeep) 외 항목을 삭제. 삭제 수 반환."""
    path = Path(root)
    if not path.exists():
        print(f"  [{root}] 없음 → 건너뜀")
        return 0

    keep = {".gitkeep"} | preserve
    items = sorted(p for p in path.iterdir() if p.name not in keep)
    kept = sorted(preserve & {p.name for p in path.iterdir()})
    keep_note = f"  (보존: {', '.join(kept)})" if kept else ""

    if not items:
        print(f"  [{root}] 삭제 대상 없음{keep_note}")
        return 0

    if dry_run:
        print(f"  [{root}] {len(items)}개 삭제 예정{keep_note}:")
        for item in items:
            print(f"    - {item.name}{'/' if item.is_dir() else ''}")
        return 0

    count = 0
    for item in items:
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        count += 1
    print(f"  [{root}] 초기화 완료 ({count}개 삭제){keep_note}")
    return count


def main():
    ap = argparse.ArgumentParser(
        prog="init.py",
        description="메모리/로그 초기화 (seed 보존). --confirm 없으면 dry-run.",
    )
    ap.add_argument("--confirm", action="store_true", help="실제 삭제 실행")
    ap.add_argument("--roots", nargs="*", default=DEFAULT_ROOTS,
                    metavar="ROOT", help=f"초기화할 root 목록 (default: {' '.join(DEFAULT_ROOTS)})")
    args = ap.parse_args()

    if not args.confirm:
        print("[dry-run] 아래 항목이 삭제됩니다. 실제 실행은 --confirm 추가.\n")
    else:
        print("[init] 초기화 시작 (seed 보존)\n")

    total = sum(_init_dir(r, dry_run=not args.confirm, preserve=PRESERVE.get(r, set()))
                for r in args.roots)

    if args.confirm:
        print(f"\n[init] 완료. 총 {total}개 삭제 (procedural_memory/DSL seed 보존).")
    else:
        print("\n[dry-run] 완료. 실제 변경 없음.")


if __name__ == "__main__":
    main()
