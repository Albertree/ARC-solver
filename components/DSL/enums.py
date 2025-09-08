from enum import Enum

class DSLType(Enum):
    TRANSFORMATION = "transformation"
    PROPERTY = "property"
    RELATION = "relation"
    UTILITY = "utility"
    UNKNOWN = "unknown"

class DSLName(Enum):
    MAKE_CANVAS = "make_canvas"
    COLORING = "coloring"
    COLOR_SWITCH = "color_switch"
    ROTATE = "rotate"
    POINT_FLIP = "point_flip"
    LINE_FLIP = "line_flip"
    MOVE = "move"
    TELEPORT = "teleport"
    CONNECT = "connect"
    STRAIGHT_LINE = "straight_line"
    RECTANGLE = "rectangle"
    CROP = "crop"
    UNKNOWN = "unknown"
