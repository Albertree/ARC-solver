from typing import NamedTuple

from .ARCKG_component import ARCKGComponent
from .grid import GRID, GRIDInfo

class PAIRInfo(NamedTuple):
    id: int
    type: str
    raw_data: dict

class PAIR(ARCKGComponent):
    def __init__(self, id:int, type:str, raw_data:dict, parent:ARCKGComponent): # , parent:ARCKGComponent, input_grid:ARCKGComponent= None, output_grid:ARCKGComponent=None):
        super().__init__(id, type)
        self.raw_data = raw_data
        self.parent = parent
        self.property = dict()
        self.program = []

    def update_property(self):
        self.childs = [self.input_grid, self.output_grid]
        self.input_grid = self.childs[0]
        self.output_grid = self.childs[1]

        self.view = [self.input_grid.view, self.output_grid.view]
        
        self.property['grid_count'] = len(self.childs)

    
    @staticmethod
    def from_json(pair_info:PAIRInfo, parent:ARCKGComponent):        
        ppp = PAIR(id=pair_info.id, type=pair_info.type, raw_data=pair_info.raw_data, parent=parent)

        for i, k in enumerate(pair_info.raw_data.keys()):
            if k == 'input':
                grid_info = GRIDInfo(
                    id = i,
                    type = 'grid', 
                    raw_data = pair_info.raw_data['input']
                )
                ggg = GRID.from_json(grid_info, parent=ppp)
                ppp.input_grid = ggg

            elif k == 'output':
                grid_info = GRIDInfo(
                    id = i,
                    type = 'grid', 
                    raw_data = pair_info.raw_data['output']
                )
                ggg = GRID.from_json(grid_info, parent=ppp)
                ppp.output_grid = ggg
        
        ppp.update_property()
        ppp.to_json()
        return ppp
    
    def to_json(self):
        import os
        import json

        pair_dict = self.property

        # PAIR_node - PAIR_property
        path = f'memory/TASK_nodes/TASK_{self.parent.hex_code}/PAIR_nodes/PAIR_{self.id}/PAIR_property'
        file_name = f'PAIR_{self.id}_property.json'
        if not os.path.exists(path):
            os.makedirs(path)
        
        with open(f'{path}/{file_name}', 'w') as f:
            json.dump(pair_dict, f, indent=2)

        # PAIR_edge
        if not os.path.exists(f'memory/TASK_nodes/TASK_{self.parent.hex_code}/PAIR_edges'):
            os.makedirs(f'memory/TASK_nodes/TASK_{self.parent.hex_code}/PAIR_edges')
        
        
    
    def __repr__(self):
        return f"PAIR({self.id}th {self.type} of TASK({self.parent.hex_code}))"
    