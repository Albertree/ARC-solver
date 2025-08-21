from ARCKG.grid_component import GridComponent
from typing import Any, Callable

class Condition:
    def __init__(self, func:Callable[[GridComponent, Any], bool],**kwargs):
        self.core_func = self._testor_func(func, **kwargs)
        self.ingredients = kwargs
        pass
    
    def _testor_func(self,func,**kwargs)->Callable:
        def wrapper(target:GridComponent):
            return func(target,**kwargs)
        return wrapper
    
    def is_satisfied(self,target:GridComponent) -> bool:
        return self.core_func(target,None)