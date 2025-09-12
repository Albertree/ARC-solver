from abc import abstractmethod
from ARCKG.grid import GRID
from .enums import DSLType, DSLName
from collections.abc import Callable


class AbstractDSL:

    def __init__(self):
        self.name = DSLName.UNKNOWN
        self.dsl_type = DSLType.UNKNOWN
        self.args:dict = {}
        self.apply_function:Callable = lambda x: x

    def execute(self,grid:GRID):
        return self.apply_function(grid,self.args)
    
    def get_args(self):
        return self.args
    
    def set_args(self, args):
        self.args = args

    def to_dict(self) : 
        return  {
            "name" : self.name,
            "dsl_type" : self.dsl_type,
            "args" : self.args,
            "apply_function" : self.apply_function
        }
    
    @abstractmethod
    def to_raw_python_string(self) :
        pass

    @abstractmethod
    def core_function(self):
        pass     

    def __str__(self):
        return str(self.name)

    def __repr__(self):
        return f"<DSL {self.name}>"
    
    def __eq__(self, other):
        return self.name == other.name
    
    def __hash__(self):
        return hash(self.name)

