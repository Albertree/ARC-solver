from ARCKG.grid import GRID
from .DSL.AbstractDSL import AbstractDSL

class Program() :
    def __init__(self, id) -> None:
        self.id = id
        self.subprograms:dict[str , Program | AbstractDSL] = {}

    def to_dict(self) -> dict:
        return {
            "id" : self.id,
            "1" : {}
        }

    def splice(self,start_idx:int, end_idx:int):
        pass

    def append(self,idx:int) : 
        pass

    def replace_subprogram(self, idx:int, new_program) :
        popped = self.subprograms[str(idx)]
        self.subprograms[str(idx)] = new_program
        return popped
    

    def execute(self,grid:GRID) -> GRID :
        for index, subprogram in enumerate(self.subprograms) :
            if isinstance(subprogram, Program) :
                grid = subprogram.execute(grid)
            elif isinstance(subprogram,AbstractDSL) : 
                grid = subprogram.execute(grid)
            else :
                raise ValueError
        
        return grid

    def __len__(self) -> int :
        return len(self.subprograms.keys())
