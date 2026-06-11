"""
process_visualizer/generate.py — 정해둔 레포(data/ARC_easy_a)의 모든 문제를 풀며
타임스텝 trace 를 잡아 data.js(window.ARBOR_DATA) 로 내보낸다. index.html 이 이걸 읽는다.

실행: python process_visualizer/generate.py   → process_visualizer/data.js
레포 바꾸려면 REPO/TASKS 만 고치면 됨.
"""

import os
import json

from tracer import build_trace   # 같은 폴더

REPO = "ARC_easy_a"
TASKS = [f"easy000{c}" for c in "abcdefghi"]


def main():
    tasks = []
    for t in TASKS:
        d = build_trace(REPO, t)
        tasks.append(d)
        print(f"  {t}: {len(d['steps'])} 타임스텝, {'✓' if d['correct'] else '✗'}")
    data = {"repo": REPO, "tasks": tasks}
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
    with open(out, "w", encoding="utf-8") as f:
        f.write("window.ARBOR_DATA = " + json.dumps(data, ensure_ascii=False) + ";")
    print(f"wrote {out}  ({len(tasks)} 문제)")


if __name__ == "__main__":
    main()
