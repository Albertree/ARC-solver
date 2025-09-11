from ..AbstractDSL import AbstractDSL
from ..enums import DSLType, DSLName
from ..ParamType import ParamType
from apply_functions import *


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


class ColoringDSL(TransformationDSL) :
    def __init__(self,apply_function=coloring):
        super().__init__(
            DSLName.COLORING, 
            ["selection", "color"], 
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR], 
            apply_function)


class ColorSwitchDSL(TransformationDSL) :
    def __init__(self,apply_function=color_switch):
        super().__init__(
            DSLName.COLOR_SWITCH,
            ["selection", "color1", "color2"], 
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR, ParamType.COLOR], 
            apply_function)



class RotateDSL(TransformationDSL) :
    def __init__(self,apply_function=rotate):
        super().__init__(
            DSLName.ROTATE, 
            ["selection", "direction", "iteration", "pivot"], 
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.ROTATE_DIRECTION, ParamType.INT, ParamType.LIST_OF_COORD_TUPLES], 
            apply_function)



class PointFlipDSL(TransformationDSL) :
    def __init__(self,apply_function=point_flip):
        super().__init__(
            DSLName.POINT_FLIP,
            ["selection", "pivot"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.LIST_OF_COORD_TUPLES],
            apply_function)



class LineFlipDSL(TransformationDSL) :
    def __init__(self,apply_function=line_flip):
        super().__init__(
            DSLName.LINE_FLIP,
            ["selection", "direction", "pivot"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.LINE_FLIP_DIRECTION, ParamType.LIST_OF_COORD_TUPLES],
            apply_function)



class MoveDSL(TransformationDSL) :
    def __init__(self,apply_function=move):
        super().__init__(
            DSLName.MOVE,
            ["selection", "direction", "distance"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.EIGHT_DIRECTION, ParamType.INT],
            apply_function)


class TeleportDSL(TransformationDSL) :
    def __init__(self,apply_function=teleport):
        super().__init__(
            DSLName.TELEPORT,
            ["selection", "grab", "destination"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.LIST_OF_COORD_TUPLES, ParamType.LIST_OF_COORD_TUPLES],
            apply_function)



class ConnectDSL(TransformationDSL) :
    def __init__(self,apply_function=connect):
        super().__init__(
            DSLName.CONNECT,
            ["selection", "color"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR],
            apply_function) 



class StraightLineDSL(TransformationDSL) :
    def __init__(self,apply_function=straight_line):
        super().__init__(
            DSLName.STRAIGHT_LINE,
            ["selection", "direction", "length", "color"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.EIGHT_DIRECTION, ParamType.INT, ParamType.COLOR],
            apply_function)



class RectangleDSL(TransformationDSL) :
    def __init__(self,apply_function=rectangle):
        super().__init__(
            DSLName.RECTANGLE,
            ["selection", "color"],
            [ParamType.LIST_OF_COORD_TUPLES, ParamType.COLOR],
            apply_function)



class CropDSL(TransformationDSL) :
    def __init__(self,apply_function=crop):
        super().__init__(
            DSLName.CROP,
            ["selection"],
            [ParamType.LIST_OF_COORD_TUPLES],
            apply_function)


