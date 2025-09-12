from enum import Enum

class DSLType(str,Enum):
    TRANSFORMATION = "transformation"
    PROPERTY = "property"
    INFORMATION = "information"
    UTILITY = "utility"
    UNKNOWN = "unknown"

class DSLName(str,Enum):
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
    LONGEST_OBJECT = "longest_object"
