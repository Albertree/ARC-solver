from DSL.AbstractDSL import AbstractDSL
from DSL.enums import DSLType, DSLName
from DSL.ParamType import ParamType
from DSL.transformation.apply_functions import *


class TransformationDSL(AbstractDSL) :
    def __init__(self, name, args_keys, args_types, apply_function):
        self.name = name
        self.dsl_type = DSLType.TRANSFORMATION
        self.args_keys = args_keys
        self.args_types = args_types
        self.apply_function = apply_function
    
    @staticmethod
    def provider(dsl_name):
        match dsl_name:
            case DSLName.MAKE_CANVAS.value:
                return MakeCanvasDSL()
            case DSLName.COLORING.value:
                return ColoringDSL()
            case DSLName.COLOR_SWITCH.value:
                return ColorSwitchDSL()
            case DSLName.ROTATE.value:
                return RotateDSL()
            case DSLName.POINT_FLIP.value:
                return PointFlipDSL()
            case DSLName.LINE_FLIP.value:
                return LineFlipDSL()
            case DSLName.MOVE.value:
                return MoveDSL()
            case DSLName.TELEPORT.value:
                return TeleportDSL()
            case DSLName.CONNECT.value:
                return ConnectDSL()
            case DSLName.STRAIGHT_LINE.value:
                return StraightLineDSL()
            case DSLName.RECTANGLE.value:
                return RectangleDSL()
            case DSLName.CROP.value:
                return CropDSL()
            case _:
                print(dsl_name,type(dsl_name), type(DSLName.MAKE_CANVAS.value))
                print(f"Error: Invalid transformation: {dsl_name}")
                return None




class MakeCanvasDSL(TransformationDSL) :
    def __init__(self, apply_function=make_canvas):
        super().__init__(
            DSLName.MAKE_CANVAS, 
            ["height", "width", "color"], 
            [ParamType.INT, ParamType.INT, ParamType.COLOR], 
            apply_function)

    def read_input_args(self):
        print("Provide 3 parameters:")
        print("1. height    (1 - 30)")
        print("2. width     (1 - 30)")
        print("3. color     (0 - 9 | 13)")
        super().read_input_args()


class ColoringDSL(TransformationDSL) :
    def __init__(self,apply_function=coloring):
        super().__init__(
            DSLName.COLORING, 
            ["selection", "color"], 
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR], 
            apply_function)

    def read_input_args(self):
        print("Provide 2 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. color     (0 - 9)")
        super().read_input_args()


class ColorSwitchDSL(TransformationDSL) :
    def __init__(self,apply_function=color_switch):
        super().__init__(
            DSLName.COLOR_SWITCH,
            ["selection", "color1", "color2"], 
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR, ParamType.COLOR], 
            apply_function)

    def read_input_args(self):
        print("Provide 3 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. color1    (0 - 9)")
        print("3. color2    (0 - 9)")
        super().read_input_args()


class RotateDSL(TransformationDSL) :
    def __init__(self,apply_function=rotate):
        super().__init__(
            DSLName.ROTATE, 
            ["selection", "direction", "iteration", "pivot"], 
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.ROTATE_DIRECTION, ParamType.INT, ParamType.LIST_OF_COORD_TUPLES], 
            apply_function)

    def read_input_args(self):
        print("Provide 4 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. direction (cw | ccw)")
        print("3. iteration (0 - N)")
        print("4. pivot     (list of coordinate tuples)")
        super().read_input_args()


class PointFlipDSL(TransformationDSL) :
    def __init__(self,apply_function=point_flip):
        super().__init__(
            DSLName.POINT_FLIP,
            ["selection", "pivot"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.LIST_OF_COORD_TUPLES],
            apply_function)

    def read_input_args(self):
        print("Provide 2 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. pivot     (list of coordinate tuples)")
        super().read_input_args()


class LineFlipDSL(TransformationDSL) :
    def __init__(self,apply_function=line_flip):
        super().__init__(
            DSLName.LINE_FLIP,
            ["selection", "direction", "pivot"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.LINE_FLIP_DIRECTION, ParamType.LIST_OF_COORD_TUPLES],
            apply_function)

    def read_input_args(self):
        print("Provide 3 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. direction (hori | verti | diag | anti)")
        print("3. pivot     (list of coordinate tuples)")
        super().read_input_args()


class MoveDSL(TransformationDSL) :
    def __init__(self,apply_function=move):
        super().__init__(
            DSLName.MOVE,
            ["selection", "direction", "distance"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.EIGHT_DIRECTION, ParamType.INT],
            apply_function)

    def read_input_args(self):
        print("Provide 3 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. direction (1,0) | (0,1) | (-1,0) | (0,-1) | (1,1) | (-1,-1) | (-1,1) | (1,-1)")
        print("3. distance  (integer)")
        super().read_input_args()


class TeleportDSL(TransformationDSL) :
    def __init__(self,apply_function=teleport):
        super().__init__(
            DSLName.TELEPORT,
            ["selection", "grab", "destination"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.LIST_OF_COORD_TUPLES, ParamType.LIST_OF_COORD_TUPLES],
            apply_function)

    def read_input_args(self):
        print("Provide 3 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. grab      (list of coordinate tuples)")
        print("3. destination (list of coordinate tuples)")
        super().read_input_args()


class ConnectDSL(TransformationDSL) :
    def __init__(self,apply_function=connect):
        super().__init__(
            DSLName.CONNECT,
            ["selection", "color"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR],
            apply_function) 

    def read_input_args(self):
        print("Provide 2 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. color     (0 - 9)")
        super().read_input_args()


class StraightLineDSL(TransformationDSL) :
    def __init__(self,apply_function=straight_line):
        super().__init__(
            DSLName.STRAIGHT_LINE,
            ["selection", "direction", "length", "color"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.EIGHT_DIRECTION, ParamType.INT, ParamType.COLOR],
            apply_function)

    def read_input_args(self):
        print("Provide 4 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. direction (1,0) | (0,1) | (-1,0) | (0,-1) | (1,1) | (-1,-1) | (-1,1) | (1,-1)")
        print("3. length    (integer)")
        print("4. color     (0 - 9)")   
        super().read_input_args()


class RectangleDSL(TransformationDSL) :
    def __init__(self,apply_function=rectangle):
        super().__init__(
            DSLName.RECTANGLE,
            ["selection", "color"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR],
            apply_function)

    def read_input_args(self):
        print("Provide 2 parameters:")
        print("1. selection (list of coordinate tuples)")
        print("2. color     (0 - 9)")
        super().read_input_args()


class CropDSL(TransformationDSL) :
    def __init__(self,apply_function=crop):
        super().__init__(
            DSLName.CROP,
            ["selection"],
            [ParamType.LIST_OF_COORD_TUPLES],
            apply_function)

    def read_input_args(self):
        print("Provide 1 parameter:")
        print("1. selection (list of coordinate tuples)")
        super().read_input_args()

