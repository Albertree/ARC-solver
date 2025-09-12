from abc import abstractmethod
from .dsl_abstract import AbstractDSL
from .enums import DSLType, DSLName


class InformationDSL(AbstractDSL) :
    def __init__(self, name, args, apply_function):
        self.name = name
        self.args = args
        self.dsl_type = DSLType.INFORMATION
        self.apply_function = apply_function
    
    @staticmethod
    def provider(dsl_name):
        match dsl_name:
            case DSLName.MAKE_CANVAS.value:
                return LongestObjectDSL()
            case _:
                print(dsl_name,type(dsl_name), type(DSLName.MAKE_CANVAS.value))
                print(f"Error: Invalid Information: {dsl_name}")
                return None
    
    @abstractmethod
    def to_raw_python_string(self):
        pass

    @abstractmethod
    def core_function():
        pass

class LongestObjectDSL(InformationDSL) :
    def __init__(self):
        super().__init__(DSLName.LONGEST_OBJECT, {}, LongestObjectDSL.core_function)

    def to_raw_python_string(self, step_number):
        return f"tfg{step_number} = {DSLName.MAKE_CANVAS}(grid=tfg{step_number-1}, selection=[], height={self.args["height"]}, width={self.args["width"]}, color_to_fill={self.args["color"]})"
        # ex) tfg1 = make_canvas(grid=tfg0, selection=[], height=1, width=1, color_to_fill=1)
    
    def core_function():
        pass
