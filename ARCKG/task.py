from typing import NamedTuple

from .ARCKG_component import ARCKGComponent
from .grid import GRID
from .pair import PAIR

class TASKInfo(NamedTuple):
    id: int
    type: str
    raw_data: dict

class TASK(ARCKGComponent):
    def __init__(self, id:int, type:str, raw_data:dict):
        super().__init__(id, type)
        self.raw_data = raw_data

        self.childs = [self.example_pairs, self.test_grid]

    def __repr__(self):
        return f"TASK(id={self.id}, type={self.type})"