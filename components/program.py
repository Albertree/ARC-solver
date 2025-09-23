from typing import Any
from ARCKG.grid import GRID
from .dsl_abstract import AbstractDSL
from .dsl_transformation import *
from .dsl_information import *
from enum import Enum

# {
#     "id" : "07fed1ed.pair_0.<program_count>",
#     "1" : {

#     },
#     "2" : {

#     },
#     ...
#     "n" : {

#     }
# }

class Program() :
    id = 0
    
    def __init__(self, id) -> None:
        self.id = id # should use new_id function for program maintainance.
        self.index = 0
        self.program_variables = ProgramVarManager("x")
        self.program_grids = ProgramVarManager("tfg")
        self.tree: ProgramNodeTree | ProgramNode = None

    ### Program property manipulation methods ### 

    def set_id(self,id:str) -> None :
        self.id= id
    
    def set_subprograms(self,subprograms) :
        self.tree = subprograms

    def append_subprogram(self,subprogram) :
        index_str = len(subprogram)+1
        self.subprograms[index_str] = subprogram

    def append(self,idx:int,subprograms:list) : 
        self.subprograms = self.subprograms[:idx]+subprograms+self.subprograms[idx:]

    def replace_subprogram(self, idx:int, new_program) :
        popped = self.subprograms[str(idx)]
        self.subprograms[str(idx)] = new_program
        return popped

    @classmethod
    def splice(self,new_id:str,start_idx:int, end_idx:int):
        spliced = Program(new_id)
        spliced.set_subprogram(self.subprograms[start_idx:end_idx])
        self.set_subprogram(self.subprograms[:start_idx]+self.set_subprograms[end_idx:])
        return spliced

    #### class parsing methods ####

    def to_dict(self) -> dict:
        dict_output = {"id" : str(self.id)}
        dict_output.update(self.subprograms_to_dict())
        return dict_output       

    def subprograms_to_dict(self) -> dict:
        dict_output = {}
        for idx, program in enumerate(self.subprograms) :
            if isinstance(program, Program) :
                dict_output[str(idx)] = program.subprograms_to_dict()
            elif isinstance(program,AbstractDSL) : 
                dict_output[str(idx)] = program.to_dict()
        
        return dict_output
    
    def to_raw_python_string(self) -> None:
        python_string = ""

        return python_string
    
    def to_python_string(self) -> None:
        python_string = ""
        for idx, program in enumerate(self.subprograms) :
            if isinstance(program, Program) :
                python_string += program.to_raw_python_string()
            elif isinstance(program,AbstractDSL) : 
                python_string += program.to_raw_python_string()
        
        return python_string

    ### Program application methods ### 

    def execute(self,grid:GRID) -> GRID :
        for subprogram in self.subprograms :
            if isinstance(subprogram, Program) :
                grid = subprogram.execute(grid)
            elif isinstance(subprogram,AbstractDSL) : 
                grid = subprogram.execute(grid)
            else :
                raise ValueError
        
        return grid

    
    ### double underscore methods ### 

    def __len__(self) -> int :
        return len(self.subprograms.keys())-1

    def __iter__(self):
        return self

    def __next__(self):
        if self.index < len(self.subprograms):
            item = self.subprograms[self.index]
            self.index += 1
            return item
        else:
            raise StopIteration


    ### Static methods ###

    @staticmethod
    def new_id():
        Program.id +=1
        return Program.id

    @staticmethod
    def merge(target1,target2) :
        # Exception fallback
        if not (isinstance(target1,Program) and isinstance(target2,Program)) :
            raise ValueError

        else :
            new_program = Program(Program.new_id())
            new_program.set_subprograms(target1.subprograms+target2.subprograms)
            return new_program

    @staticmethod
    def compare(target1,target2) : 
        # Exception fallback
        if not (isinstance(target1,Program) and isinstance(target2,Program)) :
            raise ValueError
        
        else :
            pass




class ProgramStatus(Enum) :
    INIT_NODE="init_node"
    NOT_READY = "not_ready"
    READY = "ready"
    IN_PROGRESS="in_progress"
    DONE="done"

class ProgramNode():
    def __init__(self, var_manager, grid_manager, 
                 dsl:AbstractDSL,
                 needed_var_names:list[str]=[],                 
                 ) :
        self.status = ProgramStatus.INIT_NODE if len(needed_var_names)==0 else ProgramStatus.NOT_READY
        self.var_manager:ProgramVarManager = var_manager
        self.grid_manager:ProgramVarManager = grid_manager
        self.dsl: Program | AbstractDSL = dsl
        self.needed_var_names = needed_var_names
    
    def execute(self):
        dsl_kwargs = {}
        for idx, var_name in enumerate(self.needed_var_names):
            dsl_kwargs[str(idx)] = self.var_manager.get_var(var_name)

        if isinstance(self.dsl,TransformationDSL) : 
            var_results, grid_results = self.dsl.core_function(dsl_kwargs)
            self.var_manager.update(var_results)
            self.grid_manager.update(grid_results)

        elif isinstance(self.dsl,InformationDSL) :
            pass

class ProgramNodeTree():
    def __init__(self):
        pass


class ProgramVarManager():
    registered_symbols = [] # symbols that are already in use with other ProgramVarManager instances ex) x, y, z, ...

    def __init__(self, symbol:str) :
        if symbol in ProgramVarManager.registered_symbols :
            raise ValueError
        else : 
            ProgramVarManager.registered_symbols.append(symbol)

        self.symbol = symbol # ex) x, y, z ...
        self.count = 0
        self.vars = {}
    
    def new_var_name(self) -> str:
        self.count+=1
        return self.symbol+str(self.count)
        # x1, x2, x3 ...
    
    def save_var(self,var_name:str,value) -> None:
        if not(var_name in self.vars.keys()) :
            raise SyntaxError
        
        else :
            self.vars[var_name] = value
    
    def get_var(self,var_name:str) :
        if not(var_name in self.vars.keys()) :
            raise SyntaxError
        
        else :
            return self.vars[var_name]
    
    def update(self, updates:dict[str,Any]) :
        for key in updates.keys():
            self.save_var(key,updates[key])


