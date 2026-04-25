# ARC-solver 함수 레퍼런스

## 목차
1. [진입점 (run.py / init.py)](#1-진입점)
2. [시각화 (basics/viz.py)](#2-시각화)
3. [지식 그래프 — 비교 (ARCKG/comparison.py)](#3-지식-그래프--비교)
4. [태스크 로딩 (managers/arc_manager.py)](#4-태스크-로딩)
5. [WM 디버그 (agent/wm_logger.py)](#5-wm-디버그)
6. [메모리 경로 유틸 (ARCKG/memory_paths.py)](#6-메모리-경로-유틸)
7. [스니펫 — semantic_memory 탐색](#7-스니펫--semantic_memory-탐색)

---

## 1. 진입점

### `run.py` — train / eval 실행

```
python run.py (--task HEX... | --seq FILE | --split {training,evaluation,easy})
              [--mode {train,eval}]
              [--n N] [--seed SEED]
              [--max-steps N] [--max-attempts N] [--time-budget SEC]
              [--sm-root PATH] [--trace-out PATH] [--log-out PATH]
              [--log-wm] [--quiet] [--out-dir DIR]
```

| arg | default | 설명 |
|-----|---------|------|
| `--mode` | `train` | train: 기존 memory 누적. eval: `eval_result/run_MMDD_HHMM/` 격리 실행 |
| `--task HEX...` | — | hex ID 직접 지정 (복수 가능) |
| `--seq FILE` | — | 줄당 hex 1개 파일 (`#` 주석 허용) |
| `--split` | — | 전체 split 실행 |
| `--n N` | — | `--split`에서 랜덤 N개 |
| `--seed` | `42` | `--n` 랜덤 시드 |
| `--max-steps` | `50` | SOAR 사이클 최대 스텝 |
| `--max-attempts` | `3` | 태스크당 최대 제출 횟수 |
| `--time-budget` | None | 에피소드 시간 제한(초) |
| `--sm-root` | `semantic_memory` | semantic_memory 경로 (train 전용) |
| `--trace-out PATH` | None | trace JSON 저장 |
| `--log-out PATH` | None | 결과 요약 로그 저장 (train, stdout 기본) |
| `--log-wm` | True | WM triplet 로그 출력 |
| `--quiet` | False | 진행 출력 억제 |
| `--out-dir DIR` | `run_logs` | 전체 stdout을 `MMDD_HHMM.log`로 저장할 폴더. `none`으로 끄기 |

**예시**

```bash
# 단일 태스크 (show_task 자동 출력, run_logs/MMDD_HHMM.log 자동 저장)
python run.py --task 08ed6ac7

# 복수 태스크
python run.py --task 08ed6ac7 007bbfb7

# eval 모드 (eval_result/run_MMDD_HHMM/ 자동 생성)
python run.py --mode eval --task 08ed6ac7

# training split 랜덤 10개
python run.py --split training --n 10 --seed 0

# 시퀀스 파일 + WM 로그
python run.py --seq my_tasks.txt --log-wm

# trace 저장
python run.py --task 08ed6ac7 --trace-out out/trace.json

# 출력 파일 저장 끄기
python run.py --task 08ed6ac7 --out-dir none
```

**로그 저장 동작**

| 모드 | 저장 위치 | 내용 |
|------|-----------|------|
| train | `run_logs/MMDD_HHMM.log` | 전체 stdout (WM 로그 포함, show_task 그리드 제외) |
| eval | `eval_result/run_MMDD_HHMM/run.log` | 전체 stdout (WM 로그 포함, show_task 그리드 제외) |

- 로그 첫 부분에 실행 시각, 명령어, mode, tasks, 주요 args가 헤더로 기록된다.
- show_task의 ANSI 그리드는 터미널에만 출력되고 로그 파일에는 포함되지 않는다.
- train 모드에서 `--out-dir none`으로 파일 저장을 끌 수 있다.

**로그 헤더 예시**

```
==============================================================
  [ARC-solver] 2026-04-26 05:30:17
  cmd  : run.py --task 08ed6ac7 --log-wm
  mode : train
  tasks: 08ed6ac7  (n=1)
  steps: max_steps=50  max_attempts=3
  log  : log_wm=True  quiet=False
==============================================================
```

**run_logs 폴더 구조**

```
run_logs/
  0426_0452.log    ← train 모드 전체 stdout (show_task 제외)
  0426_0510.log
  ...
```

**eval 결과 폴더 구조**

```
eval_result/
  run_0426_0355/
    semantic_memory/     ← 빈 상태에서 시작 (원본 memory 불변)
    episodic_memory/
    procedural_memory/
    run.log              ← 헤더 + WM 로그 + 태스크별 결과 (전체 stdout)
  run_0426_0411/         ← 다음 eval 실행 (독립)
    ...
```

---

### `init.py` — 메모리 초기화

```
python init.py [--sm-root PATH] [--ep-root PATH] [--proc-root PATH] [--confirm]
```

`--confirm` 없으면 dry-run (삭제 목록만 출력, 실제 변경 없음).

```bash
python init.py              # dry-run: 삭제 예정 목록 확인
python init.py --confirm    # 실제 초기화
```

---

## 2. 시각화

**위치**: `basics/viz.py`

### `show_task(task, gap=6)`

태스크 전체를 ANSI 색상으로 출력한다. example pairs는 input→output, test pairs는 input만 표시.

```python
from managers.arc_manager import ARCManager
from basics.viz import show_task

mgr = ARCManager(data_root="data", semantic_memory_root="semantic_memory")
task = mgr.load_task("08ed6ac7")
show_task(task)
```

### `show_objects(grid, cols_per_row=5, gap=3)`

Grid의 Object들을 5열씩 가로 배치해 출력한다.

```python
from basics.viz import show_objects

show_objects(task.example_pairs[0].input_grid)
show_objects(task.example_pairs[0].output_grid)
```

### `show_comparison(a, b, gap=6)`

두 컴포넌트를 가로로 나란히 출력한다. Grid, Object, Pixel 모두 가능.

```python
from basics.viz import show_comparison

pair = task.example_pairs[0]
g0, g1 = pair.input_grid, pair.output_grid

# Grid vs Grid
show_comparison(g0, g1)

# Object vs Object (같은 색 쌍)
in_obj  = [o for o in g0.objects if o.color != 0][0]
out_obj = [o for o in g1.objects if o.color != 0][0]
show_comparison(in_obj, out_obj)

# Pixel vs Pixel
show_comparison(in_obj.pixels[0], out_obj.pixels[0])

# cross-pair 비교
show_comparison(task.example_pairs[0].input_grid,
                task.example_pairs[1].input_grid)
```

---

## 3. 지식 그래프 — 비교

**위치**: `ARCKG/comparison.py`

### `compare(a, b, save=False, semantic_memory_root="semantic_memory") -> dict`

두 컴포넌트(Grid / Object / Pixel)를 비교해 관계 딕셔너리를 반환한다.

| 파라미터 | 설명 |
|----------|------|
| `a`, `b` | 비교 대상 (Grid, Object, Pixel) |
| `save` | True이면 비교 엣지를 semantic_memory에 JSON으로 저장 |
| `semantic_memory_root` | 저장 경로 |

**반환 형식**

```json
{
  "id1": "T08ed6ac7.P0.G0",
  "id2": "T08ed6ac7.P0.G1",
  "lca_node_id": "T08ed6ac7.P0",
  "order": 1,
  "result": {
    "type": "COMM | DIFF",
    "score": "2/3",
    "category": {
      "size":  {"type": "COMM", "value": ...},
      "color": {"type": "DIFF", "in": ..., "out": ...}
    }
  }
}
```

**예시**

```python
from ARCKG import compare

pair = task.example_pairs[0]

# Grid 비교
r = compare(pair.input_grid, pair.output_grid,
            save=True, semantic_memory_root="semantic_memory")
print(r["result"]["type"], r["result"]["score"])

# COMM / DIFF 속성 분류
cats = r["result"]["category"]
comm = [k for k, v in cats.items() if v["type"] == "COMM"]
diff = [k for k, v in cats.items() if v["type"] == "DIFF"]
print(f"COMM={comm}  DIFF={diff}")

# Object 비교 (같은 색 쌍)
in_map  = {o.color: o for o in pair.input_grid.objects  if o.color != 0}
out_map = {o.color: o for o in pair.output_grid.objects if o.color != 0}
for c in sorted(set(in_map) & set(out_map)):
    r = compare(in_map[c], out_map[c],
                save=True, semantic_memory_root="semantic_memory")
    print(f"color={c}: {r['result']['score']}")
```

**저장 경로 규칙**

비교 엣지 파일은 두 노드의 LCA(최소 공통 조상) 폴더 아래에 저장된다.

```
semantic_memory/
  N_T08ed6ac7/
    N_P0/
      E_G0-G1.json          ← 같은 Pair 내 Grid 비교 (LCA = P0)
      N_G0/
        E_O0-O1.json        ← 같은 Grid 내 Object 비교 (LCA = G0)
```

---

## 4. 태스크 로딩

**위치**: `managers/arc_manager.py`

### `ARCManager(data_root, semantic_memory_root)`

```python
mgr = ARCManager(data_root="data", semantic_memory_root="semantic_memory")
```

### `mgr.load_task(task_hex) -> Task`

단일 태스크 로드. ARCKG 노드 계층 구성 및 semantic_memory에 속성 파일 기록.

탐색 순서: `data/{hex}` → `data/{hex}.json` → `data/ARC_AGI/training/{hex}.json` → `data/ARC_AGI/evaluation/{hex}.json` → `data/ARC_easy/{hex}.json`

```python
task = mgr.load_task("08ed6ac7")
print(task.task_hex)                          # "08ed6ac7"
print(len(task.example_pairs))               # example pair 수
print(len(task.test_pairs))                  # test pair 수
print(task.example_pairs[0].input_grid)      # Grid 노드
```

### `mgr.load_all_tasks(split="training") -> list[Task]`

split 전체 로드. 개별 오류는 경고만 출력하고 계속 진행.

```python
tasks = mgr.load_all_tasks(split="training")    # ~400개
tasks = mgr.load_all_tasks(split="evaluation")  # ~100개
tasks = mgr.load_all_tasks(split="easy")
```

### `ARCManager.from_hex_code(task_hex, data_root, semantic_memory_root) -> Task`

클래스 메서드. ARCEnvironment 내부에서 사용.

---

## 5. WM 디버그

**위치**: `agent/wm_logger.py`

### `print_wm_triplets(wm, label="", step=0)`

WM 상태를 SOAR triplet 형식으로 출력한다. 이전 호출 이후 변경된 WME를 기호로 구분한다.

```
+  (S1 ^current-task 08ed6ac7)   ← 추가/변경된 WME
-  (S1 ^old-attr val)            ← 제거된 WME
   (S1 ^type state               ← 변화 없는 WME
       ^superstate nil)
```

모든 줄은 기호(`+`/`-`/` `) + 공백 2칸으로 시작하며 ANSI 코드 없이 순수 텍스트로 출력된다.

```python
from agent.wm_logger import print_wm_triplets, reset_wm_snapshot
from agent.wm import WorkingMemory

wm = WorkingMemory()
reset_wm_snapshot()                        # diff 기준점 초기화
print_wm_triplets(wm, "초기 상태", step=0)

wm.s1["current-task"] = "08ed6ac7"
print_wm_triplets(wm, "태스크 주입 후", step=1)
```

### `reset_wm_snapshot(wm=None)`

| 호출 방법 | 동작 |
|-----------|------|
| `reset_wm_snapshot()` | 스냅샷 비움 → 다음 print에서 전체 `+` |
| `reset_wm_snapshot(wm)` | 현재 WM 상태를 기준점으로 → 변화 없음 = 공백 prefix |

태스크 경계마다 `reset_wm_snapshot()`을 호출하면 이전 태스크의 WME가 다음 태스크 출력에 섞이지 않는다.

---

## 6. 메모리 경로 유틸

**위치**: `ARCKG/memory_paths.py`

### 노드 ID 형식

```
T{hex}                        # TASK     예: T08ed6ac7
T{hex}.P{n}                   # PAIR     예: T08ed6ac7.P0  (example)
                              #                T08ed6ac7.Pa (test)
T{hex}.P{n}.G{g}              # GRID     예: T08ed6ac7.P0.G0 (input)
                              #                T08ed6ac7.P0.G1 (output)
T{hex}.P{n}.G{g}.O{o}         # OBJECT   예: T08ed6ac7.P0.G0.O2
T{hex}.P{n}.G{g}.O{o}.X{x}   # PIXEL    예: T08ed6ac7.P0.G0.O2.X5
```

### 주요 함수

```python
from ARCKG.memory_paths import (
    node_id_to_folder_path,
    id_to_json_path,
    id_pair_to_comparison_path,
)

root = "semantic_memory"

# 노드 폴더 경로
node_id_to_folder_path("T08ed6ac7.P0.G0", root)
# → "semantic_memory/N_T08ed6ac7/N_P0/N_G0"

# 속성 파일 경로
id_to_json_path("T08ed6ac7.P0.G0", root)
# → "semantic_memory/N_T08ed6ac7/N_P0/N_G0/E_G0.json"

# 비교 엣지 파일 경로 (LCA 폴더 아래)
id_pair_to_comparison_path("T08ed6ac7.P0.G0", "T08ed6ac7.P0.G1", root)
# → "semantic_memory/N_T08ed6ac7/N_P0/E_G0-G1.json"
```

---

## 7. 스니펫 — semantic_memory 탐색

REPL이나 개발 중 semantic_memory 상태를 빠르게 확인할 때 사용하는 코드 스니펫.

### `walk_tree` — 폴더 트리 출력

```python
import os

def walk_tree(root: str, max_files: int = 50):
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        rel   = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        ind   = "  " * depth
        if rel != ".":
            print(f"{ind}{os.path.basename(dirpath)}/")
        for fname in sorted(filenames):
            if count >= max_files:
                print(f"{ind}  ... (이하 생략)")
                return
            print(f"{ind}  {fname}")
            count += 1

walk_tree("semantic_memory")
```

### `show_json` — 속성/엣지 파일 내용 출력

```python
import json

def show_json(path: str, skip_keys: tuple = ()):
    if not os.path.exists(path):
        print(f"(파일 없음: {path})")
        return
    with open(path) as f:
        data = json.load(f)
    if skip_keys:
        data = {k: v for k, v in data.items() if k not in skip_keys}
    print(json.dumps(data, indent=2, ensure_ascii=False))

# TASK 속성
show_json("semantic_memory/N_T08ed6ac7/E_T08ed6ac7.json")

# GRID 속성 (contents 생략)
show_json("semantic_memory/N_T08ed6ac7/N_P0/N_G0/E_G0.json",
          skip_keys=("contents",))

# 비교 엣지 (category 생략)
show_json("semantic_memory/N_T08ed6ac7/N_P0/E_G0-G1.json",
          skip_keys=("category",))
```

### 비교 엣지 파일 목록 출력

```python
import os

def list_edges(root: str = "semantic_memory"):
    edges = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.startswith("E_") and "-" in f:
                edges.append(os.path.relpath(os.path.join(dirpath, f), root))
    for e in sorted(edges):
        print(e)

list_edges()
```
