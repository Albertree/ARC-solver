from abc import abstractmethod
from typing import overload


from .ARCKG_component import ARCKGComponent
from .types.type import PIXELData_Type


class GridComponent(ARCKGComponent):
    def __init__(self,id:int,type:str,parent:list[ARCKGComponent]): #, pixel_data:PIXELData_Type=[]) :
        super().__init__(id, type)
        # self.pixel_data = pixel_data
        self.parent:list[ARCKGComponent] = [parent]
    
    # @abstractmethod
    # def compute_children(self) ->list[ARCKGComponent]:
    #     pass

    @abstractmethod
    def from_json(data_dict) :
        pass

    def __repr__(self) :
        #todo : implement
        return str(self.pixel_data)
