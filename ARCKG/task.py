from typing import NamedTuple

from .ARCKG_component import ARCKGComponent
from .pair import PAIR, PAIRInfo

class TASKInfo(NamedTuple):
    id: int
    type: str
    raw_data: dict

class TASK(ARCKGComponent):
    def __init__(self, id: int, type: str, raw_data: dict, hex_code: str):
        super().__init__(id, type)
        self.raw_data = raw_data
        self.hex_code = hex_code

        self.example_pairs = [self.raw_data['train']]
        self.test_pairs = [self.raw_data['test']]

        self.view = self.task_dict_to_list(self.raw_data)

        self.property = dict()

    def task_dict_to_list(self, raw_data: dict) -> list:
        view = []

        ttrain = []
        for i in range(len(raw_data['train'])):
            ttrain.append(list(raw_data['train'][i].values()))
        ttest = []
        for i in range(len(raw_data['test'])):
            ttest.append(list(raw_data['test'][i].values()))

        for pair in ttrain:
            view.append(pair)
        for pair in ttest:
            view.append(pair)
                   
        return view

    def update_property(self):
        self.example_pair_count = len(self.example_pairs) 
        self.test_pair_count = len(self.test_pairs)

        self.childs = self.example_pairs
        self.train = self.example_pairs
        self.test = self.test_pairs

        self.view_example = self.view[:self.example_pair_count]
        self.view_test = self.view[self.example_pair_count:]

        self.property['example_pair_count'] = self.example_pair_count
        self.property['test_pair_count'] = self.test_pair_count

    @staticmethod
    def from_json(task_info:TASKInfo, task_hex_code: str):
        ttt = TASK(id=task_info.id, type=task_info.type, raw_data=task_info.raw_data, hex_code=task_hex_code)
        ttt.update_property()
    
        # Create example pairs
        example_pairs = []
        for i, example in enumerate(task_info.raw_data['train']):
            example_pair_info = PAIRInfo(
                id=i,
                type='example',
                raw_data=example
            )
            pair = PAIR.from_json(example_pair_info, parent=ttt)
            example_pairs.append(pair)
        
        # Create test pairs
        test_pairs = []
        for i, test in enumerate(task_info.raw_data['test']):
            test_pair_info = PAIRInfo(
                id=i,
                type='test',
                raw_data=test
            )
            pair = PAIR.from_json(test_pair_info, parent=ttt)
            test_pairs.append(pair)

        # Set the pairs in the task
        ttt.example_pairs = example_pairs
        ttt.test_pairs = test_pairs
        
        # Update task properties
        ttt.update_property()
        ttt.to_json()
        return ttt
    
    def to_json(self):
        import os
        import json
        from .memory_paths import task_node_dir, task_property_path

        task_dict = self.property
        task_path = task_node_dir(self.hex_code)
        if not os.path.exists(task_path):
            os.makedirs(task_path)

        # TASK property (self-pointing edge): E_T{hex}.json
        prop_path = task_property_path(self.hex_code)
        with open(prop_path, 'w') as f:
            json.dump(task_dict, f, indent=2)
        
        # Create integrated ARCKG JSON
        # self.create_integrated_arckg_json()
    
    def create_integrated_arckg_json(self):
        """Create integrated ARCKG JSON file with all components"""
        import os
        import json
        
        # Initialize the integrated structure
        integrated_arckg = {
            "id": self.hex_code,
            "type": "TASK",
            "data": {},
            "property": self.property,
            "PAIR_edges": {},
            "PAIR_nodes": {}
        }
        
        # Add pairs
        for i, pair in enumerate(self.example_pairs + self.test_pairs):
            pair_data = {
                "id": f"{self.hex_code}.PAIR_nodes.{i}",
                "type": "PAIR",
                "data": {},
                "property": pair.property,
                "GRID_edges": {},
                "GRID_nodes": {}
            }
            
            # Add grids for each pair
            if hasattr(pair, 'input_grid') and pair.input_grid:
                grid_data = self._create_grid_data(pair.input_grid, pair.id, 0, f"{self.hex_code}.PAIR_nodes.{i}")
                pair_data["GRID_nodes"]["0"] = grid_data
            
            if hasattr(pair, 'output_grid') and pair.output_grid:
                grid_data = self._create_grid_data(pair.output_grid, pair.id, 1, f"{self.hex_code}.PAIR_nodes.{i}")
                pair_data["GRID_nodes"]["1"] = grid_data
            
            integrated_arckg["PAIR_nodes"][str(i)] = pair_data
        
        # Save integrated ARCKG JSON (optional; under task node)
        from .memory_paths import task_node_dir
        arcgk_path = task_node_dir(self.hex_code)
        if not os.path.exists(arcgk_path):
            os.makedirs(arcgk_path)
        
        arcgk_file = f'{arcgk_path}ARCKG_{self.hex_code}.json'
        with open(arcgk_file, 'w') as f:
            json.dump(integrated_arckg, f, indent=2)
    
    def _create_grid_data(self, grid, pair_id, grid_id, pair_path):
        """Create grid data structure for integrated ARCKG"""
        grid_data = {
            "id": f"{pair_path}.GRID_nodes.{grid_id}",
            "type": "GRID",
            "data": {},
            "property": grid.property,
            "OBJECT_edges": {},
            "OBJECT_nodes": {},
            "PIXEL_edges": {},
            "PIXEL_nodes": {}
        }
        
        # Add objects
        if hasattr(grid, 'objects') and grid.objects:
            for obj in grid.objects:
                obj_data = {
                    "id": f"{pair_path}.GRID_nodes.{grid_id}.OBJECT_nodes.{obj.id}",
                    "type": "OBJECT",
                    "data": {},
                    "property": obj.property,
                    "PIXEL_edges": {},
                    "PIXEL_nodes": {}
                }
                
                # Add pixels for each object
                if hasattr(obj, 'pixels') and obj.pixels:
                    for pixel in obj.pixels:
                        pixel_data = {
                            "id": f"{pair_path}.GRID_nodes.{grid_id}.OBJECT_nodes.{obj.id}.PIXEL_nodes.{pixel.id}",
                            "type": "PIXEL",
                            "data": {},
                            "property": pixel.property
                        }
                        obj_data["PIXEL_nodes"][str(pixel.id)] = pixel_data
                
                grid_data["OBJECT_nodes"][str(obj.id)] = obj_data
        
        # Add pixels directly under grid
        if hasattr(grid, 'pixels') and grid.pixels:
            for pixel in grid.pixels:
                pixel_data = {
                    "id": f"{pair_path}.GRID_nodes.{grid_id}.PIXEL_nodes.{pixel.id}",
                    "type": "PIXEL",
                    "data": {},
                    "property": pixel.property
                }
                grid_data["PIXEL_nodes"][str(pixel.id)] = pixel_data
        
        return grid_data

    def __repr__(self):
        return f"TASK(id={self.id}, type={self.type}, hex_code={self.hex_code}, example_pairs={len(self.example_pairs)}, test_pairs={len(self.test_pairs)})"