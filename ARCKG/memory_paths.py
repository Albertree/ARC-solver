"""
Memory storage path helpers.
Convention: folders = nodes (N_*), JSON files = edges/properties (E_*).

LTM roots (SOAR-style):
- Semantic: semantic_memory/  (node structure, properties, comparison edges)
- Procedural: procedural_memory/  (production rules, chunks)
- Episodic: episodic_memory/  (task-solving episodes)

Semantic root: semantic_memory/
- TASK: semantic_memory/N_T{hex}/
- TASK property (self-edge): semantic_memory/N_T{hex}/E_T{hex}.json
- PAIR: semantic_memory/N_T{hex}/N_P{pair_id}/  (train: 0,1,2 ; test: a,b,c,...)
- PAIR property: semantic_memory/N_T{hex}/N_P{pair_id}/E_P{pair_id}.json
- GRID: semantic_memory/N_T{hex}/N_P{pair_id}/N_G{grid_id}/
- GRID property: semantic_memory/N_T{hex}/N_P{pair_id}/N_G{grid_id}/E_G{grid_id}.json
- OBJECT: .../N_G{grid_id}/N_O{obj_id}/
- OBJECT property: .../N_O{obj_id}/E_O{obj_id}.json
- PIXEL: .../N_X{pixel_id}/ with E_X{pixel_id}.json
"""

# Semantic memory: node structure, properties, comparison edges (current storage)
MEMORY_ROOT = "semantic_memory/"
# Alias for code that referred to "semantic" root by this name
SEMANTIC_MEMORY_ROOT = MEMORY_ROOT

# Procedural memory: production rules, chunks (condition → operator)
PROCEDURAL_MEMORY_ROOT = "procedural_memory/"

# Episodic memory: task-solving episodes (state, operator, result sequences)
EPISODIC_MEMORY_ROOT = "episodic_memory/"


def task_node_dir(hex_code: str) -> str:
    """TASK node folder: semantic_memory/N_T{hex}/"""
    return f"{MEMORY_ROOT}N_T{hex_code}/"


def task_property_path(hex_code: str) -> str:
    """TASK property (self-edge) file: semantic_memory/N_T{hex}/E_T{hex}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/E_T{hex_code}.json"


def pair_node_dir(hex_code: str, pair_id: "int | str") -> str:
    """PAIR node folder: semantic_memory/N_T{hex}/N_P{pair_id}/ (pair_id: train 0,1,2 or test a,b,c,...)"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/"


def pair_property_path(hex_code: str, pair_id: "int | str") -> str:
    """PAIR property file: semantic_memory/N_T{hex}/N_P{pair_id}/E_P{pair_id}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/E_P{pair_id}.json"


def grid_node_dir(hex_code: str, pair_id: "int | str", grid_id: int) -> str:
    """GRID node folder: semantic_memory/N_T{hex}/N_P{pair_id}/N_G{grid_id}/"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/N_G{grid_id}/"


def grid_property_path(hex_code: str, pair_id: "int | str", grid_id: int) -> str:
    """GRID property file: .../N_G{grid_id}/E_G{grid_id}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/N_G{grid_id}/E_G{grid_id}.json"


def object_node_dir(hex_code: str, pair_id: "int | str", grid_or_tf: str, grid_id: int, obj_id: int) -> str:
    """OBJECT node folder. grid_or_tf is 'G' (GRID)."""
    base = f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/N_{grid_or_tf}{grid_id}/"
    return f"{base}N_O{obj_id}/"


def object_property_path(hex_code: str, pair_id: "int | str", grid_or_tf: str, grid_id: int, obj_id: int) -> str:
    """OBJECT property file: .../N_O{obj_id}/E_O{obj_id}.json"""
    return f"{object_node_dir(hex_code, pair_id, grid_or_tf, grid_id, obj_id)}E_O{obj_id}.json"


def pixel_node_dir(hex_code: str, pair_id: "int | str", grid_or_tf: str, grid_id: int, pixel_id: int) -> str:
    """PIXEL node folder under GRID."""
    base = f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/N_{grid_or_tf}{grid_id}/"
    return f"{base}N_X{pixel_id}/"


def pixel_property_path(hex_code: str, pair_id: "int | str", grid_or_tf: str, grid_id: int, pixel_id: int) -> str:
    """PIXEL property file: .../N_X{pixel_id}/E_X{pixel_id}.json"""
    return f"{pixel_node_dir(hex_code, pair_id, grid_or_tf, grid_id, pixel_id)}E_X{pixel_id}.json"


def pixel_under_object_dir(hex_code: str, pair_id: "int | str", grid_or_tf: str, grid_id: int, obj_id: int, pixel_id: int) -> str:
    """PIXEL node folder under OBJECT."""
    base = f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_id}/N_{grid_or_tf}{grid_id}/N_O{obj_id}/"
    return f"{base}N_X{pixel_id}/"


def pixel_under_object_property_path(hex_code: str, pair_id: "int | str", grid_or_tf: str, grid_id: int, obj_id: int, pixel_id: int) -> str:
    """PIXEL property file under OBJECT: .../N_O{obj_id}/N_X{pixel_id}/E_X{pixel_id}.json"""
    return f"{pixel_under_object_dir(hex_code, pair_id, grid_or_tf, grid_id, obj_id, pixel_id)}E_X{pixel_id}.json"


# --- Comparison (optional) edge paths: E_* for between-node edges ---

def edge_pair_comparison_path(hex_code: str, pair_num1: str, pair_num2: str, score: int = 0) -> str:
    """PAIR-PAIR comparison edge. Stored under task: N_T{hex}/E_P{p1}-P{p2}.json (score in content or filename)."""
    return f"{MEMORY_ROOT}N_T{hex_code}/E_P{pair_num1}-P{pair_num2}.json"


def edge_grid_comparison_path(hex_code: str, pair_num: str, grid_num1: str, grid_num2: str, score: int = 0) -> str:
    """GRID-GRID comparison edge. Under pair: N_T{hex}/N_P{p}/E_G{g1}-G{g2}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_num}/E_G{grid_num1}-G{grid_num2}.json"


def edge_object_comparison_path(hex_code: str, pair_num: str, grid_num: str, obj_num1: str, obj_num2: str, score: int = 0) -> str:
    """OBJECT-OBJECT comparison edge. Under pair (grid-level edges): N_T{hex}/N_P{p}/E_O{o1}-O{o2}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_num}/E_O{obj_num1}-O{obj_num2}.json"


def edge_pixel_comparison_path_grid(hex_code: str, pair_num: str, grid_num: str, pixel_num1: str, pixel_num2: str, score: int = 0) -> str:
    """PIXEL-PIXEL comparison (grid direct). Under pair: N_T{hex}/N_P{p}/E_X{x1}-X{x2}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_num}/E_X{pixel_num1}-X{pixel_num2}.json"


def edge_pixel_comparison_path_object(hex_code: str, pair_num: str, grid_num: str, obj_num: str, pixel_num1: str, pixel_num2: str, score: int = 0) -> str:
    """PIXEL-PIXEL comparison (under object). Under grid: N_T{hex}/N_P{p}/N_G{g}/N_O{o}/E_X{x1}-X{x2}.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/N_P{pair_num}/N_G{grid_num}/N_O{obj_num}/E_X{pixel_num1}-X{pixel_num2}.json"


def edge_task_comparison_path(hex_1: str, hex_2: str) -> str:
    """TASK-TASK comparison edge. At root: semantic_memory/E_T{hex1}-T{hex2}.json"""
    return f"{MEMORY_ROOT}E_T{hex_1}-T{hex_2}.json"


def edge_task_level_comparison_path(hex_code: str, label1: str, label2: str) -> str:
    """PAIR 간 비교 등 task 노드 바로 아래에 저장할 엣지. 예: N_T{hex}/E_P0G0-P1G0.json"""
    return f"{MEMORY_ROOT}N_T{hex_code}/E_{label1}-{label2}.json"
