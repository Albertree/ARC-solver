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
    def __init__(self, id) -> None:
        self.id = ""
        self.index = 0
        self.subprograms:list[Program | AbstractDSL] = []

    def set_id(self,id:str) -> None :
        self.id= id
    
    def set_subprograms(self,subprograms) :
        self.subprograms = subprograms

    def append_subprogram(self,subprogram) :
        index_str = len(subprogram)+1
        self.subprograms[index_str] = subprogram

    def to_dict(self) -> dict:
        dict_output = {"id" : str(self.id)}
        dict_output.update(self.subprograms_to_dict())
        

    def subprograms_to_dict(self) -> dict:
        dict_output = {}
        for idx, program in enumerate(self.subprograms) :
            if isinstance(program, Program) :
                dict_output[str(idx)] = program.subprograms_to_dict()
            elif isinstance(program,AbstractDSL) : 
                dict_output[str(idx)] = program.to_dict()
        
        return dict_output

    def append(self,idx:int,subprograms:list) : 
        self.subprograms = self.subprograms[:idx]+subprograms+self.subprograms[idx:]

    def replace_subprogram(self, idx:int, new_program) :
        popped = self.subprograms[str(idx)]
        self.subprograms[str(idx)] = new_program
        return popped
    

    def execute(self,grid:GRID) -> GRID :
        for subprogram in self.subprograms :
            if isinstance(subprogram, Program) :
                grid = subprogram.execute(grid)
            elif isinstance(subprogram,AbstractDSL) : 
                grid = subprogram.execute(grid)
            else :
                raise ValueError
        
        return grid

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

    @classmethod
    def splice(self,new_id:str,start_idx:int, end_idx:int):
        spliced = Program(new_id)
        spliced.set_subprogram(self.subprograms[start_idx:end_idx])
        self.set_subprogram(self.subprograms[:start_idx]+self.set_subprograms[end_idx:])
        return spliced


def main() :
