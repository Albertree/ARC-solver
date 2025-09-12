from abc import abstractmethod
from .dsl_abstract import AbstractDSL
from .enums import DSLType, DSLName
from .dsl_param_type import ParamType
from apply_functions import *


class TransformationDSL(AbstractDSL) :
    def __init__(self, name, args, apply_function):
        self.name = name
        self.args = args
        self.dsl_type = DSLType.TRANSFORMATION
        self.apply_function = apply_function
    
    @staticmethod
    def provider(dsl_name: DSLName, **kwargs):
        match dsl_name:
            case DSLName.MAKE_CANVAS:
                return MakeCanvasDSL(**kwargs)
            case DSLName.COLORING:
                return ColoringDSL(**kwargs)
            case DSLName.COLOR_SWITCH:
                return ColorSwitchDSL(**kwargs)
            case DSLName.ROTATE:
                return RotateDSL(**kwargs)
            case DSLName.POINT_FLIP:
                return PointFlipDSL(**kwargs)
            case DSLName.LINE_FLIP:
                return LineFlipDSL(**kwargs)
            case DSLName.MOVE:
                return MoveDSL(**kwargs)
            case DSLName.TELEPORT:
                return TeleportDSL(**kwargs)
            case DSLName.CONNECT:
                return ConnectDSL(**kwargs)
            case DSLName.STRAIGHT_LINE:
                return StraightLineDSL(**kwargs)
            case DSLName.RECTANGLE:
                return RectangleDSL(**kwargs)
            case DSLName.CROP:
                return CropDSL(**kwargs)
            case _:
                raise ValueError(f"Unknown DSL name: {dsl_name}")
    
    @abstractmethod
    def to_raw_python_string(self):
        pass


class MakeCanvasDSL(TransformationDSL):
    def __init__(self, 
                 height:ParamType.INT,
                 width:ParamType.INT,
                 color:ParamType.COLOR):
        args = {
            "height" : height,
            "width" : width,
            'color' : color
        }
        super().__init__(DSLName.MAKE_CANVAS, args, make_canvas)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.MAKE_CANVAS}(grid=tfg{step_number-1}, selection=[], height={self.args['height']}, width={self.args['width']}, color_to_fill={self.args['color']})"
        # ex) tfg1 = make_canvas(grid=tfg0, selection=[], height=1, width=1, color_to_fill=1)

    
    def core_function(self): #make_canvas
        height = self.args['height']
        width = self.args['width']
        color_to_fill = self.args['color']
        
        layer = make_layer()
        for i in range(height):
            for j in range(width):
                layer[30 + i][30 + j] = color_to_fill
        return layer  



class ColoringDSL(TransformationDSL):
    def __init__(self, 
                 selection:ParamType.LIST_OF_COORD_TUPLES, 
                 color:ParamType.COLOR):
        args = {
            'selection' : selection,
            'color' : color,            
            }
        super().__init__(DSLName.COLORING, args, coloring)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.COLORING}(grid=tfg{step_number-1}, selection={self.args['selection']}, color={self.args['color']})"
        # ex) tfg1 = coloring(grid=tfg0, selection=[(1,2), (3,4)], color=1)

    
    def core_function(self) :
        raise NotImplementedError


class ColorSwitchDSL(TransformationDSL):
    def __init__(self, 
                 selection:ParamType.LIST_OF_COORD_TUPLES, 
                 color_from:ParamType.COLOR, 
                 color_to:ParamType.COLOR):
        args = {
            'selection' : selection,
            'color_from' : color_from,
            'color_to' : color_to
        }
        super().__init__(DSLName.COLOR_SWITCH, args, color_switch)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.COLOR_SWITCH}(grid=tfg{step_number-1}, selection={self.args['selection']}, from={self.args['color_from']}, to={self.args['color_to']})"
        # ex) tfg1 = color_switch(grid=tfg=0, selection=[(1,2), (3,4)], color_from=1, color_to=2)
    
    
    def core_function(self) :
        raise NotImplementedError


class RotateDSL(TransformationDSL):
    def __init__(self, 
                 selection:ParamType.LIST_OF_COORD_TUPLES, 
                 direction:ParamType.ROTATE_DIRECTION, 
                 iteration:ParamType.INT, 
                 pivot:ParamType.COORD_TUPLE):
        args = {
            'selection' : selection,
            'direction' : direction,
            'iteration' : iteration,
            "pivot": pivot,
        }
        super().__init__(DSLName.ROTATE, args, rotate)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.ROTATE}(grid=tfg{step_number-1}, selection={self.args['selection']}, direction={self.args['direction']}, iteration={self.args['iteration']}, pivot={self.args["pivot"]})"
        # ex) tfg1 = rotate(grid=tfg0, selection=[(1,2), (3,4)], direction="cw", iteration=1, pivot=(1,1))
    
    
    def core_function(self) :
        raise NotImplementedError


class LineFlipDSL(TransformationDSL):
    def __init__(self, 
                 selection:ParamType.LIST_OF_COORD_TUPLES, 
                 direction:ParamType.LINE_FLIP_DIRECTION, 
                 pivot:ParamType.COORD_TUPLE):
        args = {
            'selection' : selection,
            'direction' : direction,
            "pivot": pivot,
        }
        super().__init__(DSLName.LINE_FLIP, args, line_flip)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.LINE_FLIP}(grid=tfg{step_number-1}, selection={self.args['selection']}, direction={self.args['direction']}, pivot={self.args["pivot"]})"
    
    
    def core_function(self) :
        raise NotImplementedError


class PointFlipDSL(TransformationDSL):
    def __init__(self, 
                 selection:ParamType.LIST_OF_COORD_TUPLES, 
                 pivot:ParamType.COORD_TUPLE):
        args = {
            'selection' : selection,
            "pivot": pivot,
        }
        super().__init__(DSLName.POINT_FLIP, args, point_flip)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.POINT_FLIP}(grid=tfg{step_number-1}, selection={self.args['selection']},pivot={self.args["pivot"]})"
    
    
    def core_function(self) :
        raise NotImplementedError


class MoveDSL(TransformationDSL):
    def __init__(self,
                 selection:ParamType.LIST_OF_COORD_TUPLES,
                 direction:ParamType.EIGHT_DIRECTION,
                 distance:ParamType.INT):
        args = {
            'selection': selection,
            'direction': direction,
            'distance': distance
        }
        super().__init__(DSLName.MOVE, args, move)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.MOVE}(grid=tfg{step_number-1}, selection={self.args['selection']}, direction={self.args['direction']}, distance={self.args['distance']})"
        # ex) tfg1 = move(grid=tfg0, selection=[(1,2),(2,3)], direction="up", distance=2)
    
    
    def core_function(self) :
        raise NotImplementedError


class TeleportDSL(TransformationDSL):
    def __init__(self,
                 selection:ParamType.LIST_OF_COORD_TUPLES,
                 grab:ParamType.LIST_OF_COORD_TUPLES,
                 destination:ParamType.COORD_TUPLE):
        args = {
            'selection': selection,
            'grab': grab,
            'destination': destination
        }
        super().__init__(DSLName.TELEPORT, args, teleport)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.TELEPORT}(grid=tfg{step_number-1}, selection={self.args['selection']}, grab={self.args['grab']}, destination={self.args['destination']})"
        # ex) tfg1 = teleport(grid=tfg0, selection=[(1,2)], grab=[(2,3)], destination=(4,4))

    
    def core_function(self) :
        raise NotImplementedError


class ConnectDSL(TransformationDSL):
    def __init__(self,
                 selection:ParamType.LIST_OF_COORD_TUPLES,
                 color:ParamType.COLOR):
        args = {
            'selection': selection,
            'color': color
        }
        super().__init__(DSLName.CONNECT, args, connect)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.CONNECT}(grid=tfg{step_number-1}, selection={self.args['selection']}, color={self.args['color']})"
        # ex) tfg1 = connect(grid=tfg0, selection=[(1,2),(3,3)], color=5)

    
    def core_function(self) :
        raise NotImplementedError


class StraightLineDSL(TransformationDSL):
    def __init__(self,
                 selection:ParamType.LIST_OF_COORD_TUPLES,
                 direction:ParamType.EIGHT_DIRECTION,
                 length:ParamType.INT,
                 color:ParamType.COLOR):
        args = {
            'selection': selection,
            'direction': direction,
            "length": length,
            'color': color
        }
        super().__init__(DSLName.STRAIGHT_LINE, args, straight_line)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.STRAIGHT_LINE}(grid=tfg{step_number-1}, selection={self.args['selection']}, direction={self.args['direction']}, length={self.args['length']}, color={self.args['color']})"
        # ex) tfg1 = straight_line(grid=tfg0, selection=[(0,0)], direction="right", length=3, color=2)
    
    
    def core_function(self) :
        raise NotImplementedError


class RectangleDSL(TransformationDSL):
    def __init__(self,
                 selection:ParamType.LIST_OF_COORD_TUPLES,
                 color:ParamType.COLOR):
        args = {
            'selection': selection,
            'color': color
        }
        super().__init__(DSLName.RECTANGLE, args, rectangle)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.RECTANGLE}(grid=tfg{step_number-1}, selection={self.args['selection']}, color={self.args['color']})"
        # ex) tfg1 = rectangle(grid=tfg0, selection=[(1,1),(2,2)], color=3)

    
    def core_function(self) :
        raise NotImplementedError


class CropDSL(TransformationDSL):
    def __init__(self,
                 selection:ParamType.LIST_OF_COORD_TUPLES):
        args = {
            'selection': selection
        }
        super().__init__(DSLName.CROP, args, crop)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.CROP}(grid=tfg{step_number-1}, selection={self.args['selection']})"
        # ex) tfg1 = crop(grid=tfg0, selection=[(0,0),(2,2)])
    
    
    def core_function(self) :
        raise NotImplementedError
