from ARCKG.pair import PAIR
from components.transformation_history import TFHistory
from components.transformation import Transformation


class TFGenerator :
    def __init__(self,task_pairs:list[PAIR]):
        self.task_pairs:list[PAIR] = task_pairs
        self.pair_pointer:int = 0
        pass

    def is_done_iteration(self) ->bool:
        return self.pair_pointer >= len(self.task_pairs)

    def get_next_pair_tfhistory(self) -> TFHistory:
        if self.is_done_iteration() :
            raise RuntimeError
            return
        
        return self.generate_tfhistory(self.task_pairs[self.pair_pointer])
        
    def generate_tfhistory(self,pair:PAIR) ->TFHistory:
        """
        Analyze the input-output pair and generate a transformation history
        that describes how to convert the input grid to the output grid.
        """
        input_grid = pair.input_grid
        output_grid = pair.output_grid
        
        # For now, create a basic transformation history with the input grid
        # and an empty list of transformations
        # This can be enhanced with actual transformation detection algorithms
        
        # Detect transformations by comparing input and output grids
        transformations = self._detect_transformations(input_grid, output_grid)
        
        # Create and return the transformation history
        tf_history = TFHistory(
            pair=pair,
            grid=input_grid,  # Starting with the input grid
            tf_history=transformations
        )
        
        return tf_history
    
    def _detect_transformations(self, input_grid, output_grid) -> list[Transformation]:
        """
        Detect what transformations were applied between input and output grids.
        This is a placeholder implementation that can be enhanced with actual
        transformation detection algorithms.
        """
        transformations = []
        
        # Basic analysis - compare grid dimensions
        input_shape = (len(input_grid.raw_data), len(input_grid.raw_data[0]) if input_grid.raw_data else 0)
        output_shape = (len(output_grid.raw_data), len(output_grid.raw_data[0]) if output_grid.raw_data else 0)
        
        # Check for common transformation types
        if input_shape != output_shape:
            # Grid size transformation detected
            transformations.append(GridResizeTransformation(input_shape, output_shape))
        
        # Check for color changes (simplified analysis)
        if self._has_color_changes(input_grid, output_grid):
            transformations.append(ColorTransformation())
        
        # If no specific transformations detected, add a generic one
        if not transformations:
            transformations.append(GenericTransformation(input_grid, output_grid))
        
        return transformations
    
    def _has_color_changes(self, input_grid, output_grid) -> bool:
        """Check if there are color changes between input and output grids"""
        if not input_grid.raw_data or not output_grid.raw_data:
            return False
        
        # Simple check: compare some cells (can be made more sophisticated)
        for i in range(min(len(input_grid.raw_data), len(output_grid.raw_data))):
            for j in range(min(len(input_grid.raw_data[i]), len(output_grid.raw_data[i]))):
                if input_grid.raw_data[i][j] != output_grid.raw_data[i][j]:
                    return True
        return False


# Basic transformation implementations
class GridResizeTransformation(Transformation):
    """Transformation that handles grid size changes"""
    def __init__(self, from_shape, to_shape):
        super().__init__()
        self.from_shape = from_shape
        self.to_shape = to_shape
    
    def execute(self):
        # Implementation for grid resizing
        return f"Resize from {self.from_shape} to {self.to_shape}"


class ColorTransformation(Transformation):
    """Transformation that handles color changes"""
    def __init__(self):
        super().__init__()
    
    def execute(self):
        # Implementation for color transformations
        return "Color transformation applied"


class GenericTransformation(Transformation):
    """Generic transformation for unclassified changes"""
    def __init__(self, input_grid, output_grid):
        super().__init__()
        self.input_grid = input_grid
        self.output_grid = output_grid
    
    def execute(self):
        # Generic transformation implementation
        return "Generic transformation applied" 