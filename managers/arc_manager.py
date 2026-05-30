"""
ARCManager — data/ 폴더에서 ARC 태스크를 로드하고 ARCKG 노드 계층을 구축.
"""

import json
import os

from ARCKG.task import Task
from ARCKG.pair import Pair
from ARCKG.grid import Grid


class ARCManager:
    """
    INTENT: 지정된 data/ 경로에서 ARC JSON 파일을 읽어
            Task → Pair → Grid → Object → Pixel 노드 계층을 구성하고
            각 노드의 to_json()/save()를 호출해 semantic_memory에 속성을 기록한다.
    MUST NOT: data/ 파일을 수정하지 마 (read-only).
              solve 로직을 여기에 포함하지 마.
    REF: ARCKG/task.py, ARCKG/pair.py, ARCKG/grid.py
         CLAUDE.md § Data, § Edge Creation Timing
    """

    def __init__(self, data_root: str = "data",
                 semantic_memory_root: str = "semantic_memory"):
        """
        INTENT: data 경로와 semantic_memory 경로로 초기화.
        MUST NOT: 생성자에서 파일을 읽지 마.
        REF: ARC-solver/managers/arc_manager.py ARCManager._build_task_mapping (line 6)
        """
        self.data_root = data_root
        self.semantic_memory_root = semantic_memory_root

    def get_task_hex(self, task_file: str) -> str:
        """
        INTENT: 태스크 파일명에서 hex ID를 추출해 반환한다.
                확장자(.json) 및 경로 prefix를 제거한 순수 파일명.
        MUST NOT: 파일을 열지 마 — 파일명 파싱만.
        REF: CLAUDE.md § Node ID format
        """
        basename = os.path.basename(task_file)
        return basename.replace(".json", "")

    def load_task(self, task_file: str) -> Task:
        """
        INTENT: data_root/{task_file}.json을 읽어 Task 노드를 생성하고
                하위 Pair/Grid/Object/Pixel 노드를 모두 구성한 뒤 반환한다.
                각 노드의 save()를 호출해 semantic_memory에 속성 파일을 기록한다.
        MUST NOT: comparison edge(E_*-*.json)를 여기서 생성하지 마
                  — 속성 파일(0th-order)만.
        REF: ARCKG/task.py Task, ARCKG/memory_paths.py
             CLAUDE.md § Edge Creation Timing
             ARC-solver/managers/arc_manager.py ARCManager.from_hex_code (line 40)
             ARC-solver/ARCKG/task.py TASK.from_json (line 59)
        """
        task_hex = self.get_task_hex(task_file)
        raw_data = self._load_raw(task_file)

        example_pairs = self._build_pairs(
            task_hex=task_hex,
            pairs_raw=raw_data["train"],
            pair_type="example",
            id_offset=0,
        )
        test_pairs = self._build_pairs(
            task_hex=task_hex,
            pairs_raw=raw_data["test"],
            pair_type="test",
            id_offset=0,
            test=True,
        )

        task = Task(
            task_hex=task_hex,
            example_pairs=example_pairs,
            test_pairs=test_pairs,
        )
        # Lazy: load 시점엔 디스크 저장(task.save) 안 함. ARCKG = 영속화된 WM 이며,
        # descend 가 방문·확정한 노드만 추후 flush (persisted WM 모델). object/pixel 도
        # 미생성 — Slice 1 은 GRID 에서 끝남 (SLICE_1_DEV §5).
        return task

    def _resolve_path(self, task_file: str) -> str:
        """data_root 아래 후보 경로에서 task json 실제 경로를 찾는다."""
        task_hex = self.get_task_hex(task_file)
        candidates = [
            os.path.join(self.data_root, task_file),
            os.path.join(self.data_root, f"{task_file}.json"),
            os.path.join(self.data_root, "ARC_AGI", "training", f"{task_hex}.json"),
            os.path.join(self.data_root, "ARC_AGI", "evaluation", f"{task_hex}.json"),
            os.path.join(self.data_root, "ARC_easy", f"{task_hex}.json"),
            os.path.join(self.data_root, "ARC_easy_a", f"{task_hex}.json"),
            os.path.join(self.data_root, f"{task_hex}.json"),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        raise FileNotFoundError(f"Task '{task_hex}' not found under '{self.data_root}'")

    def _load_raw(self, task_file: str) -> dict:
        """task json 원본 dict 로드."""
        with open(self._resolve_path(task_file), "r") as f:
            return json.load(f)

    def test_ground_truth(self, task_file: str) -> list:
        """env 채점용 — test pair 정답 출력(raw)을 순서대로 반환한다.
        이 값은 에이전트의 Task(ARCKG)에는 절대 들어가지 않는다 (컨닝 방지)."""
        raw = self._load_raw(task_file)
        return [p.get("output") for p in raw.get("test", [])]

    def _build_pairs(self, task_hex: str, pairs_raw: list,
                     pair_type: str, id_offset: int,
                     test: bool = False) -> list[Pair]:
        """
        ARC JSON의 train/test 목록에서 Pair 노드 목록을 구성한다.
        - example pairs: pair_id = "T{hex}.P0", "T{hex}.P1", ...
        - test pairs:    pair_id = "T{hex}.Pa", "T{hex}.Pb", ...
        test pair 의 output(G1)은 *만들지 않는다* — 정답은 에이전트가 예측해야 하며
        env 가 test_ground_truth() 로 따로 채점한다.
        """
        pairs = []
        for idx, raw_pair in enumerate(pairs_raw):
            if test:
                p_suffix = chr(ord("a") + idx)  # a, b, c, ...
            else:
                p_suffix = str(idx)             # 0, 1, 2, ...

            pair_id = f"T{task_hex}.P{p_suffix}"

            # Input grid (항상 존재). Lazy: extract_objects() 안 부름 — Slice 1 은
            # GRID 에서 끝나므로 object/pixel 미생성 (필요 시 descend 가 추후 생성).
            input_id = f"{pair_id}.G0"
            input_grid = Grid(grid_id=input_id, raw=raw_pair["input"])

            # Output grid: test pair 는 정답을 숨긴다(output_grid=None). example 만 구성.
            output_grid = None
            if not test:
                output_raw = raw_pair.get("output")
                if output_raw is not None and len(output_raw) > 0 and len(output_raw[0]) > 0:
                    output_id = f"{pair_id}.G1"
                    output_grid = Grid(grid_id=output_id, raw=output_raw)

            pair = Pair(pair_id=pair_id, input_grid=input_grid, output_grid=output_grid)
            pairs.append(pair)
        return pairs

    @classmethod
    def from_hex_code(
        cls,
        task_hex: str,
        data_root: str = "data",
        semantic_memory_root: str = "semantic_memory",
    ) -> "Task":
        """hex ID로 단일 태스크를 로드해 반환한다."""
        return cls(data_root, semantic_memory_root).load_task(task_hex)

    def load_all_tasks(self, split: str = "training") -> list:
        """
        INTENT: data_root/{split}/ 아래 모든 태스크 파일을 순회하며
                load_task()를 호출해 Task 목록을 반환한다.
        MUST NOT: 에러 발생 시 전체를 중단하지 마 — 개별 태스크 오류는 로그만.
        REF: ARC-solver/managers/arc_manager.py ARCManager._build_task_mapping (line 6)
             ARC-solver/basics/ARCLOADER.py ARCDataset.load_data (line 15)
        """
        # ARC_AGI 하위 split 폴더 우선 탐색, 없으면 data_root 직접
        candidate_dirs = [
            os.path.join(self.data_root, "ARC_AGI", split),
            os.path.join(self.data_root, split),
            self.data_root,
        ]
        split_dir = None
        for d in candidate_dirs:
            if os.path.isdir(d):
                split_dir = d
                break
        if split_dir is None:
            raise FileNotFoundError(
                f"Split directory '{split}' not found under '{self.data_root}'"
            )

        json_files = sorted(
            f for f in os.listdir(split_dir) if f.endswith(".json")
        )

        tasks = []
        for filename in json_files:
            try:
                task = self.load_task(os.path.join(split_dir, filename))
                tasks.append(task)
            except Exception as e:
                print(f"[ARCManager] Warning: failed to load '{filename}': {e}")
        return tasks
