"""
OBJECT node — GRID 아래 연결 성분(connected component).
Node ID 형식: T{hex}.P{p}.G{g}.O{o}
"""

import json
import os

from ARCKG.memory_paths import id_to_json_path, node_id_to_folder_path


class Object:
    """
    INTENT: hodel objects() 함수로 검출된 하나의 object.
            colorgrid(bbox 크기, 투명=13)와 격자 내 절대 좌표 pos로 초기화.
            8개 property(area/color/coordinate/method/position/shape/size/symmetry)를
            to_json()으로 직렬화한다.
    MUST NOT: GRID 전체를 저장하지 마. bbox 범위만 가진다.
    REF: ARC-solver/ARCKG/object.py OBJECT.update_property (line 170)
         ARC-solver/DSL/object_finder.py find_all_objects (line 62)
    """

    def __init__(self, object_id: str, colorgrid: list, pos: tuple, method: dict):
        """
        Args:
            object_id:  전체 node_id 문자열 (e.g. "T0a.P0.G0.O3")
            colorgrid:  list[list[int]], bbox 크기. 투명 셀 = 13.
            pos:        (row_min, col_min) — bbox left_top 절대 좌표
            method:     {"univalued": bool, "diagonal": bool, "without_bg": bool}
        """
        self.node_id = object_id
        self.colorgrid = colorgrid
        self.pos = pos
        self.method = method
        self.pixels: list = []  # Pixel 객체 목록 (object-level)

        # --- transformation DSL selection 인터페이스 ---
        h = len(colorgrid)
        w = len(colorgrid[0]) if colorgrid else 0
        row_min, col_min = pos

        # bbox: colorgrid 의 별칭 (transformation.py 에서 selection.bbox 로 접근)
        self.bbox = colorgrid

        # coordinate: 비투명 셀의 절대 (row, col) 목록
        self.coordinate = [
            (row_min + r, col_min + c)
            for r, row in enumerate(colorgrid)
            for c, cell in enumerate(row)
            if cell != 13
        ]

        # bbox 내 전체 (row, col) — teleport 에서 grab 검증에 사용
        self.bbox_coordinate = [
            (row_min + r, col_min + c)
            for r in range(h)
            for c in range(w)
        ]

        # 꼭짓점 절대 좌표
        self.left_top     = (row_min,         col_min)
        self.right_top    = (row_min,         col_min + w - 1)
        self.left_bottom  = (row_min + h - 1, col_min)
        self.right_bottom = (row_min + h - 1, col_min + w - 1)

        # --- 하위 호환 속성 (bounding_box, mask, color) ---
        self.bounding_box = (row_min, col_min, row_min + h - 1, col_min + w - 1)
        self.mask = [[cell != 13 for cell in row] for row in colorgrid]
        colors = [cell for row in colorgrid for cell in row if cell != 13]
        self.color = max(set(colors), key=colors.count) if colors else 0

    # ------------------------------------------------------------------ #
    #  대칭성 헬퍼 — dihedral 모듈의 변환을 자기 자신과 비교             #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _hori_symmetry(grid: list) -> bool:
        """좌우(수직 축) 대칭 — flip_h 적용해도 동일."""
        from procedural_memory.type_system.dihedral import flip_h
        return flip_h(grid) == grid

    @staticmethod
    def _verti_symmetry(grid: list) -> bool:
        """상하(수평 축) 대칭 — flip_v 적용해도 동일."""
        from procedural_memory.type_system.dihedral import flip_v
        return flip_v(grid) == grid

    @staticmethod
    def _diag_symmetry(grid: list) -> bool:
        """주 대각선 대칭 (정사각형 전용)."""
        from procedural_memory.type_system.dihedral import flip_diag
        return flip_diag(grid) == grid

    @staticmethod
    def _anti_symmetry(grid: list) -> bool:
        """반 대각선 대칭 (정사각형 전용)."""
        from procedural_memory.type_system.dihedral import flip_anti
        return flip_anti(grid) == grid

    # ------------------------------------------------------------------ #
    #  직렬화                                                               #
    # ------------------------------------------------------------------ #

    def to_json(self) -> dict:
        """
        8개 OBJECT property dict 반환 (schema에 맞게 정규화):

        area       : int                          — bbox 내 비투명(0-9) 셀 수
        color      : set<class<color>>            — 등장 색 NAME 정렬 리스트
        coordinate : set<tuple<int,int>>          — 비투명 셀의 절대 (row,col) 집합
                                                    (순서 무관, 표현은 정렬된 list로 직렬화)
        method     : {univalued/diagonal/without_bg : bool}
        position   : {left_top/right_top/left_bottom/right_bottom : tuple<int,int>}
        shape      : list<list<bool>>             — 비투명=True, 투명=False
        size       : {height: int, width: int}
        symmetry   : {hori/verti/diag/anti_symm : bool}
        """
        from procedural_memory.type_system import value_to_name

        h = len(self.colorgrid)
        w = len(self.colorgrid[0]) if self.colorgrid else 0
        row_min, col_min = self.pos

        # color: 등장 색의 NAME 정렬 리스트
        present = sorted({
            cell for row in self.colorgrid for cell in row if 0 <= cell <= 9
        })
        color_set = [value_to_name(v) for v in present]

        # coordinate: 비투명 셀의 절대 (row, col) tuple 목록
        coordinate = [
            (row_min + r, col_min + c)
            for r, row in enumerate(self.colorgrid)
            for c, cell in enumerate(row)
            if cell != 13
        ]

        # shape: bool mask (True=비투명, False=투명)
        shape = [[cell != 13 for cell in row] for row in self.colorgrid]

        # area
        area = sum(1 for row in shape for v in row if v)

        # position: 4 코너 tuple
        position = {
            "left_top":     (row_min,         col_min),
            "right_top":    (row_min,         col_min + w - 1),
            "left_bottom":  (row_min + h - 1, col_min),
            "right_bottom": (row_min + h - 1, col_min + w - 1),
        }

        # symmetry
        hori_symm  = self._hori_symmetry(self.colorgrid)
        verti_symm = self._verti_symmetry(self.colorgrid)
        if h == w:
            diag_symm = self._diag_symmetry(self.colorgrid)
            anti_symm = self._anti_symmetry(self.colorgrid)
        else:
            diag_symm = False
            anti_symm = False

        return {
            "area":       area,
            "color":      color_set,
            "coordinate": coordinate,
            "method":     self.method,
            "position":   position,
            "shape":      shape,
            "size":       {"height": h, "width": w},
            "symmetry": {
                "hori_symm":  hori_symm,
                "verti_symm": verti_symm,
                "diag_symm":  diag_symm,
                "anti_symm":  anti_symm,
            },
        }

    def save(self, semantic_memory_root: str):
        """to_json()을 E_O{o}.json으로 기록하고, 하위 Pixel도 모두 save."""
        folder = node_id_to_folder_path(self.node_id, semantic_memory_root)
        os.makedirs(folder, exist_ok=True)
        path = id_to_json_path(self.node_id, semantic_memory_root)
        with open(path, "w") as f:
            json.dump({"id": self.node_id, "result": self.to_json()}, f, indent=2)
        for pixel in self.pixels:
            pixel.save(semantic_memory_root)

    def __repr__(self) -> str:
        return (f"Object(id={self.node_id}, color={self.color}, "
                f"pos={self.pos}, pixels={len(self.pixels)})")
