from tracemalloc import start
from ARCKG.grid import GRID
from .DSLClasses.AbstractDSL import AbstractDSL
from .DSLClasses.transformation.classes import *

# {
#     "id" : "asdfsfa",
#     "1" : {

#     },
#     "2" : {

#     },
#     ...
#     "n" : {

#     }
# }

class Program() :
    id = 1

    def __init__(self, id) -> None:
        self.id = id
        raise NotImplementedError # should use new_id function for program maintainance.
        self.index = 0
        self.subprograms:list[Program | AbstractDSL] = []

    ### Program property manipulation methods ### 

    def set_id(self,id:str) -> None :
        self.id= id
    
    def set_subprograms(self,subprograms) :
        self.subprograms = subprograms

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