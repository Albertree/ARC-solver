"""
NODE_SCHEMAS — 각 ARCKG 노드의 속성별 타입 선언.

비교 함수는 노드 종류를 보고 이 schema를 조회해서
각 속성에 어떤 타입 의미로 비교할지 결정한다.

타입 표기는 문자열로 통일 (저장과 코드 형식 일치):
  "int"
  "bool"
  "class<color>"
  "tuple<int,int>"
  "list<T>", "set<T>", "list<list<class<color>>>" 등 컨테이너 합성
"""

NODE_SCHEMAS = {
    "TASK": {
        "example_pair_count": "int",
        "test_pair_count":    "int",
    },

    "PAIR": {
        "grid_count": "int",
    },

    "GRID": {
        "size": {
            "height": "int",
            "width":  "int",
        },
        "color":    "set<class<color>>",
        "contents": "grid",
    },

    "OBJECT": {
        "area":       "int",
        "color":      "set<class<color>>",
        "coordinate": "set<tuple<int,int>>",
        "method": {
            "univalued":  "bool",
            "diagonal":   "bool",
            "without_bg": "bool",
        },
        "position": {
            "left_top":     "tuple<int,int>",
            "right_top":    "tuple<int,int>",
            "left_bottom":  "tuple<int,int>",
            "right_bottom": "tuple<int,int>",
        },
        "shape": "shape",
        "size": {
            "height": "int",
            "width":  "int",
        },
        "symmetry": {
            "hori_symm":  "bool",
            "verti_symm": "bool",
            "diag_symm":  "bool",
            "anti_symm":  "bool",
        },
    },

    "PIXEL": {
        "color":      "class<color>",
        "coordinate": "tuple<int,int>",
    },
}


def get_node_schema(node_kind: str) -> dict:
    """노드 종류 문자열로 schema 조회. 미등록 노드는 빈 dict."""
    return NODE_SCHEMAS.get(node_kind, {})
