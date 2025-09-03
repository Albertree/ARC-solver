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
        pair_path = f'memory/TASK_nodes/TASK_{self.parent.hex_code}/PAIR_nodes/PAIR_{self.id}/'
        if not os.path.exists(pair_path):
            os.makedirs(pair_path)

        # PAIR_node - PAIR_property
        path = f'{pair_path}/PAIR_property'
        file_name = f'PAIR_{self.id}_property.json'
        if not os.path.exists(path):
            os.makedirs(path)
        
        with open(f'{path}/{file_name}', 'w') as f:
            json.dump(pair_dict, f, indent=2)

         # PAIR_edge
        pair_edge_path = f'memory/TASK_nodes/TASK_{self.parent.hex_code}/'
        pair_edge_path += f'PAIR_edges'
        if not os.path.exists(pair_edge_path):
            os.makedirs(pair_edge_path)
        
        # Update integrated ARCKG JSON
        # self.update_integrated_arckg_json()
    
    def update_integrated_arckg_json(self):
        """Update the integrated ARCKG JSON with pair information"""
        import os
        import json
        
        arckg_file = f'memory/TASK_nodes/ARCKG_{self.parent.hex_code}.json'
        
        # Check if integrated ARCKG file exists
        if not os.path.exists(arckg_file):
            return
        
        try:
            with open(arckg_file, 'r') as f:
                integrated_arckg = json.load(f)
            
            # Find and update the pair data
            pair_id_str = f"({self.parent.hex_code}, {self.id}, None, None, None, 'pair')"
            
            # Check if pair already exists
            pair_exists = False
            if str(self.id) in integrated_arckg["PAIR_nodes"]:
                pair_data = integrated_arckg["PAIR_nodes"][str(self.id)]
                if pair_data["id"] == pair_id_str:
                    # Update existing pair
                    pair_data["property"] = self.property
                    pair_exists = True
            
            # If pair doesn't exist, add it
            if not pair_exists:
                pair_data = {
                    "id": pair_id_str,
                    "type": "PAIR",
                    "data": {},
                    "property": self.property,
                    "GRID_edges": {},
                    "GRID_nodes": {}
                }
                integrated_arckg["PAIR_nodes"][str(self.id)] = pair_data
            
            # Save updated integrated ARCKG JSON
            with open(arckg_file, 'w') as f:
                json.dump(integrated_arckg, f, indent=2)
                
        except Exception as e:
            print(f"Error updating integrated ARCKG JSON: {e}")
    
    def __repr__(self):
        return f"PAIR({self.id}th {self.type} of TASK({self.parent.hex_code}))"
    