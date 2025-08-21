from .ARCKG_component import ARCKGComponent
from .grid_component import GridComponent
from typing import NamedTuple
from .types.type import PIXELData_Type

class PIXELInfo(NamedTuple):
    id: int
    type: str
    raw_data: PIXELData_Type

class PIXEL(GridComponent):
    def __init__(self, id:int, type:str, parent:list, raw_data:PIXELData_Type): #, pixel_data:PIXELData_Type):
        super().__init__(id, type, parent)
        self.raw_data = raw_data

    def update_property(self, pixel):
        self.colorgrid = [[pixel[0]]]
        self.colcoord = [pixel]
        
        self.view = self.colorgrid
        
        self.color = pixel[0][0]
        self.coordinate = pixel[0][1]
        self.row_index = pixel[0][1][0]
        self.col_index = pixel[0][1][1]

    @staticmethod
    def from_json(pixel_info:PIXELInfo, parent:ARCKGComponent):
        xxx = PIXEL(id=pixel_info.id, type=pixel_info.type, raw_data=pixel_info.raw_data, parent=[parent])
        xxx.update_property(pixel_info.raw_data)

        return xxx

    def __repr__(self):
        return f"PIXEL({self.color}, {self.coordinate})"