from typing import NamedTuple

from .grid import GRID, GRIDInfo
from .ARCKG_component import ARCKGComponent

class PAIRInfo(NamedTuple):
    id: int
    type: str
    raw_data: dict

class PAIR(ARCKGComponent):
    def __init__(self, id:int, type:str, raw_data:dict, parent:ARCKGComponent): # , parent:ARCKGComponent, input_grid:ARCKGComponent= None, output_grid:ARCKGComponent=None):
        super().__init__(id, type)
        self.raw_data = raw_data
        self.parent = parent

    def update_property(self):
        self.childs = [self.input_grid, self.output_grid]
        self.input_grid = self.childs[0]
        self.output_grid = self.childs[1]

        self.view = [self.input_grid.view, self.output_grid.view]
        
    
    @staticmethod
    def from_json(pair_info:PAIRInfo, parent:ARCKGComponent):        
        ppp = PAIR(id=pair_info.id, type=pair_info.type, raw_data=pair_info.raw_data, parent=parent)

        for i, k in enumerate(pair_info.raw_data.keys()):
            if k == 'input':
                grid_info = GRIDInfo(
                    id = i,
                    type = 'input', 
                    raw_data = pair_info.raw_data['input']
                )
                ggg = GRID.from_json(grid_info, parent=ppp)
                ppp.input_grid = ggg

            elif k == 'output':
                grid_info = GRIDInfo(
                    id = i,
                    type = 'output', 
                    raw_data = pair_info.raw_data['output']
                )
                ggg = GRID.from_json(grid_info, parent=ppp)
                ppp.output_grid = ggg
        
        ppp.update_property()

        return ppp
    
    def compute_children(self):
        # GRID 의 child (OBJECT) 들을 불러와 자신의 property 중 children 에 저장합니다.
        # For now, return empty list - this can be implemented later with actual pixel/object detection
        # pixels = [...]
        # self.children = pixels
        if hasattr(self, 'parent') and self.parent and len(self.parent) > 0:
            print(f"GRID parent ID: {self.parent[0].id}")
        
        # Return empty list for now - can be implemented with actual child components later
        return []
    
    def __repr__(self):
        return f"PAIR({self.id}th {self.type} of TASK({self.parent.task_hex_code}))"
    