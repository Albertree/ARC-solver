"""
ARC-solver 메모리 초기화.

--confirm 없이 실행하면 dry-run (삭제 예정 목록 출력만).
--confirm 있어야 실제 파일 삭제.

사용법:
  python init.py               dry-run (변경 없음, 목록만 출력)
  python init.py --confirm     실제 초기화 실행
"""

import argparse
import shutil
from pathlib import Path


def _parse_args():
    p = argparse.ArgumentParser(
        prog="init.py",
        description="메모리 초기화. --confirm 없이 실행 시 dry-run.",
    )
    p.add_argument(
        "--sm-root", default="semantic_memory", dest="sm_root",
        metavar="PATH", help="semantic_memory 루트 (default: semantic_memory)",
    )
    p.add_argument(
        "--ep-root", default="episodic_memory", dest="ep_root",
        metavar="PATH", help="episodic_memory 루트 (default: episodic_memory)",
    )
    p.add_argument(
        "--proc-root", default="procedural_memory", dest="proc_root",
        metavar="PATH", help="procedural_memory 루트 (default: procedural_memory)",
    )
    p.add_argument(
        "--confirm", action="store_true",
        help="실제 삭제 실행 (없으면 dry-run)",
    )
    return p.parse_args()


def _init_dir(root: str, dry_run: bool) -> int:
    """
    root/ 아래 .gitkeep 제외 모든 항목 삭제.
    dry_run=True이면 삭제 목록만 출력하고 0 반환.
    실제 삭제 후 삭제된 항목 수 반환.
    """
    path = Path(root)
    if not path.exists():
        print(f"  [{root}] 없음 → 건너뜀")
        return 0

    items = sorted(p for p in path.iterdir() if p.name != ".gitkeep")
    if not items:
        print(f"  [{root}] 이미 비어있음")
        return 0

    if dry_run:
        print(f"  [{root}] {len(items)}개 항목 삭제 예정:")
        for item in items:
            suffix = "/" if item.is_dir() else ""
            print(f"    - {item.name}{suffix}")
        return 0

    count = 0
    for item in items:
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
        count += 1
    print(f"  [{root}] 초기화 완료 ({count}개 삭제)")
    return count


def main():
    args = _parse_args()
    roots = [args.sm_root, args.ep_root, args.proc_root]

    if not args.confirm:
        print("[dry-run] 아래 항목이 삭제됩니다. 실제 삭제하려면 --confirm을 추가하세요.\n")
    else:
        print("[init] 메모리 초기화 시작\n")

    total = 0
    for root in roots:
        total += _init_dir(root, dry_run=not args.confirm)

    if args.confirm:
        print(f"\n[init] 완료. 총 {total}개 항목 삭제됨.")
    else:
        print("\n[dry-run] 완료. 실제 변경 없음.")


if __name__ == "__main__":
    main()
