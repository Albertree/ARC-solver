def rgb(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def rgb_bg(r, g, b, text):
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{r};{g};{b}m{text}\033[0m"

def color_text(index, text):
    COLORS = {
        0: (0, 0, 0),         # black
        1: (0, 116, 217),     # blue
        2: (255, 65, 54),     # red
        3: (46, 204, 64),     # green
        4: (255, 220, 0),     # yellow
        5: (170, 170, 170),   # gray
        6: (240, 18, 190),    # pink
        7: (255, 133, 27),    # orange
        8: (127, 219, 255),   # light blue
        9: (135, 12, 37),     # dark red
        10: (128, 0, 128),    # purple
        11: (0, 128, 128),    # teal
        12: (101, 67, 33),    # brown
        13: (214, 255, 255),  # white
        14: (79, 79, 79)      # dark gray
    }
    r, g, b = COLORS.get(index, (255, 255, 255))
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{r};{g};{b}m{text}\033[0m"

# =============================================================================
# MAIN PRINT FUNCTION
# =============================================================================

def printcg(data, wait_for_enter=True):
    """Main function to print colored grid data with automatic type detection.
    ARC_AGENT_MODE=1 이면: 엔터 대기 없음, 화면 클리어 없음 → 터미널에 로그가 주욱 쌓임.
    """
    import os
    agent_mode = bool(os.environ.get("ARC_AGENT_MODE"))
    if agent_mode:
        wait_for_enter = False
        print("\n" + "─" * 50)  # 구분선: 이전 출력과 구분, 스크롤 시 보기 쉽게
    else:
        print("\033[2J\033[H", end='')
    
    # Case 1: Task view structure (input/output pairs)
    if detect_task_view(data):
        print_task_view(data)
        print()
        if wait_for_enter:
            print("Press Enter to continue...", end='')
            input()
        return
    
    # Case 2: Object list (list of objects)
    if detect_object_list(data):
        print_object_list(data, wait_for_enter)
        return
    
    # Case 3: Single pixel object
    if detect_pixel(data):
        print_pixel(data, wait_for_enter)
        return
    
    # Case 4: Single pair object (input/output)
    if detect_pair(data):
        print_pair(data, wait_for_enter)
        return
    
    # Case 5: Single grid object
    if detect_grid(data):
        print_grid(data, wait_for_enter)
        return
    
    # Case 6: Single object (non-pixel, non-grid)
    if detect_object(data):
        print_object(data, wait_for_enter)
        return
    
    # Case 7: Raw grid data (2D array)
    if detect_raw_grid(data):
        print_raw_grid(data)
        print()
        if wait_for_enter:
            print("Press Enter to continue...", end='')
            input()
        return
    
    # Case 8: Multiple grids (list of 2D arrays)
    if detect_multiple_grids(data):
        print_multiple_grids(data)
        print()
        if wait_for_enter:
            print("Press Enter to continue...", end='')
            input()
        return
    
    # Case 9: Complex nested structure
    if isinstance(data, list):
        grids = extract_grids_from_nested(data)
        if grids:
            print_multiple_grids(grids)
            print()
            if wait_for_enter:
                print("Press Enter to continue...", end='')
                input()
            return
    
    # Case 10: Object with view attribute
    if detect_object_with_view(data):
        print_raw_grid(data.view)
        print()
        if wait_for_enter:
            print("Press Enter to continue...", end='')
            input()
        return
    
    # Case 11: Object with raw_data attribute
    if detect_object_with_raw_data(data):
        print_raw_grid(data.raw_data)
        print()
        if wait_for_enter:
            print("Press Enter to continue...", end='')
            input()
        return
    
    # Default case: No displayable data
    print()
    if wait_for_enter:
        print("Press Enter to continue...", end='')
        input()

# =============================================================================
# DETECTION FUNCTIONS (detect_*)
# =============================================================================

def detect_task_view(data):
    """Detect if data is a task view structure (list of input/output pairs)"""
    if not isinstance(data, list) or len(data) == 0:
        return False
    
    for pair in data:
        if not isinstance(pair, list) or len(pair) != 2:
            return False
        for grid in pair:
            if not detect_raw_grid(grid):
                return False
    
    return True

def detect_object_list(data):
    """Detect if data is a list of objects with grid data"""
    if not isinstance(data, list) or len(data) == 0:
        return False
    
    for item in data:
        if hasattr(item, 'view') and detect_raw_grid(item.view):
            return True
        if hasattr(item, 'raw_data'):
            try:
                if hasattr(item, 'object_colcoord_to_colorgrid'):
                    grid_data = item.object_colcoord_to_colorgrid(item.raw_data)
                    if detect_raw_grid(grid_data):
                        return True
            except:
                pass
        if hasattr(item, 'type') and item.type == 'pixel':
            return True
    
    return False

def detect_pixel(data):
    """Detect if data is a pixel object"""
    return hasattr(data, 'type') and data.type == 'pixel'

def detect_pair(data):
    """Detect if data is a pair object"""
    return hasattr(data, 'type') and data.type == 'pair'

def detect_grid(data):
    """Detect if data is a grid object"""
    return hasattr(data, 'type') and data.type == 'grid'

def detect_object(data):
    """Detect if data is a generic object"""
    return hasattr(data, 'type') and data.type == 'object'

def detect_raw_grid(data):
    """Detect if data is a valid 2D grid array"""
    if not isinstance(data, list) or not data:
        return False
    if not isinstance(data[0], list):
        return False
    row_length = len(data[0])
    for row in data:
        if not isinstance(row, list) or len(row) != row_length:
            return False
        if not all(isinstance(cell, int) for cell in row):
            return False
    return True

def detect_multiple_grids(data):
    """Detect if data is a list of grids"""
    if not isinstance(data, list):
        return False
    return all(detect_raw_grid(item) for item in data)

def detect_object_with_view(data):
    """Detect if object has view attribute with grid data"""
    return hasattr(data, 'view') and detect_raw_grid(data.view)

def detect_object_with_raw_data(data):
    """Detect if object has raw_data attribute with grid data"""
    return hasattr(data, 'raw_data') and detect_raw_grid(data.raw_data)

# =============================================================================
# PRINT FUNCTIONS (print_*)
# =============================================================================

def print_task_view(data):
    """Print task view structure (input/output pairs)"""
    for i, pair in enumerate(data):
        if i > 0:
            print()
            print()
        
        input_grid = pair[0]
        output_grid = pair[1]
        max_height = max(len(input_grid), len(output_grid))
        
        for row_idx in range(max_height):
            if row_idx < len(input_grid):
                input_row = ''.join(color_text(val, "  ") for val in input_grid[row_idx])
            else:
                input_row = " " * (len(input_grid[0]) * 2) if input_grid and input_grid[0] else ""
            
            if row_idx < len(output_grid):
                output_row = ''.join(color_text(val, "  ") for val in output_grid[row_idx])
            else:
                output_row = " " * (len(output_grid[0]) * 2) if output_grid and output_grid[0] else ""
            
            print(f"{input_row}      {output_row}")

def print_object_list(object_list, wait_for_enter=True):
    """Print list of objects with numbering"""
    for i, obj in enumerate(object_list):
        if i > 0:
            print()
            print()
        
        print(f"{i+1}.")
        
        if detect_pixel(obj):
            print_pixel(obj, wait_for_enter=False)
            continue
        
        grid_data = extract_grid_from_object(obj)
        if grid_data:
            print_raw_grid(grid_data)
        else:
            print("  " * 5)
    
    print()
    if wait_for_enter:
        print("Press Enter to continue...", end='')
        input()

def print_pixel(pixel_obj, wait_for_enter=True):
    """Print pixel object as colored block"""
    grid_data = extract_grid_from_pixel(pixel_obj)
    
    if grid_data:
        print_raw_grid(grid_data)
    else:
        try:
            if hasattr(pixel_obj, 'color'):
                color_val = pixel_obj.color
                if isinstance(color_val, int):
                    print(color_text(color_val, "  "))
                else:
                    print("  ")
            else:
                print("  ")
        except:
            print("  ")
    
    if wait_for_enter:
        print("Press Enter to continue...", end='')
        input()

def print_pair(pair_obj, wait_for_enter=True):
    """Print pair object (input/output grids)"""
    if hasattr(pair_obj, 'view') and isinstance(pair_obj.view, list) and len(pair_obj.view) == 2:
        input_grid = pair_obj.view[0]
        output_grid = pair_obj.view[1]
        
        if detect_raw_grid(input_grid) and detect_raw_grid(output_grid):
            max_height = max(len(input_grid), len(output_grid))
            
            for row_idx in range(max_height):
                if row_idx < len(input_grid):
                    input_row = ''.join(color_text(val, "  ") for val in input_grid[row_idx])
                else:
                    input_row = " " * (len(input_grid[0]) * 2) if input_grid and input_grid[0] else ""
                
                if row_idx < len(output_grid):
                    output_row = ''.join(color_text(val, "  ") for val in output_grid[row_idx])
                else:
                    output_row = " " * (len(output_grid[0]) * 2) if output_grid and output_grid[0] else ""
                
                print(f"{input_row}      {output_row}")
    
    print()
    if wait_for_enter:
        print("Press Enter to continue...", end='')
        input()

def print_grid(grid_obj, wait_for_enter=True):
    """Print grid object"""
    if hasattr(grid_obj, 'view') and detect_raw_grid(grid_obj.view):
        print_raw_grid(grid_obj.view)
    elif hasattr(grid_obj, 'raw_data') and detect_raw_grid(grid_obj.raw_data):
        print_raw_grid(grid_obj.raw_data)
    else:
        print("  " * 5)
    
    print()
    if wait_for_enter:
        print("Press Enter to continue...", end='')
        input()

def print_object(obj, wait_for_enter=True):
    """Print generic object"""
    grid_data = extract_grid_from_object(obj)
    
    if grid_data:
        print_raw_grid(grid_data)
    else:
        print("  " * 5)
    
    print()
    if wait_for_enter:
        print("Press Enter to continue...", end='')
        input()

def print_raw_grid(grid_data):
    """Print raw grid data (2D array)"""
    for row in grid_data:
        print(''.join(color_text(val, "  ") for val in row))

def print_multiple_grids(grids):
    """Print multiple grids side by side"""
    max_height = max(len(grid) for grid in grids if grid) if grids else 0
    
    for i in range(max_height):
        row_segments = []
        for grid in grids:
            if i < len(grid):
                row_segments.append(''.join(color_text(val, "  ") for val in grid[i]))
            else:
                row_segments.append("")
        print("    ".join(row_segments))


def print_grids_side_by_side(labels, grids, gap="    "):
    """Print labeled grids in one row (test input | output | gt output).
    labels: list of 3 strings. grids: list of 3 raw 2D grids (or None for missing)."""
    if not grids or len(grids) != 3:
        return
    # Normalize: get .view or raw; replace None with empty grid
    raw = []
    for g in grids:
        if g is None:
            raw.append([])
        elif hasattr(g, "view") and detect_raw_grid(getattr(g, "view", None)):
            raw.append(g.view)
        elif detect_raw_grid(g):
            raw.append(g)
        else:
            raw.append([])
    # Width of each grid in chars (2 chars per cell)
    widths = [(2 * len(r[0]) if r and r[0] else 0) for r in raw]
    max_height = max(len(r) for r in raw) if raw else 0
    # Print label line (center label under each grid)
    label_line_parts = []
    for i, lbl in enumerate(labels):
        w = widths[i]
        if len(lbl) > w:
            lbl = lbl[: w - 2] + ".."
        label_line_parts.append(lbl.center(w) if w else lbl)
    print(gap.join(label_line_parts))
    if max_height == 0:
        print("(no grids)")
        return
    # Print grids row by row
    for row_idx in range(max_height):
        row_segments = []
        for i, grid in enumerate(raw):
            if row_idx < len(grid):
                row_segments.append(''.join(color_text(val, "  ") for val in grid[row_idx]))
            else:
                row_segments.append(" " * (widths[i] if i < len(widths) else 0))
        print(gap.join(row_segments))

# =============================================================================
# EXTRACTION FUNCTIONS (extract_*)
# =============================================================================

def extract_grids_from_nested(data):
    """Extract all grids from nested data structure"""
    grids = []
    def find_grids(item):
        if detect_raw_grid(item):
            grids.append(item)
        elif isinstance(item, list):
            for sub_item in item:
                find_grids(sub_item)
    find_grids(data)
    return grids

def extract_grid_from_object(obj):
    """Extract grid data from object"""
    if hasattr(obj, 'view') and detect_raw_grid(obj.view):
        return obj.view
    elif hasattr(obj, 'raw_data') and hasattr(obj, 'object_colcoord_to_colorgrid'):
        try:
            grid_data = obj.object_colcoord_to_colorgrid(obj.raw_data)
            if detect_raw_grid(grid_data):
                return grid_data
        except:
            pass
    return None

def extract_grid_from_pixel(pixel_obj):
    """Extract grid data from pixel object"""
    if hasattr(pixel_obj, 'view') and detect_raw_grid(pixel_obj.view):
        return pixel_obj.view
    elif hasattr(pixel_obj, 'colorgrid') and detect_raw_grid(pixel_obj.colorgrid):
        return pixel_obj.colorgrid
    elif hasattr(pixel_obj, 'raw_data'):
        try:
            if hasattr(pixel_obj, 'object_colcoord_to_colorgrid'):
                grid_data = pixel_obj.object_colcoord_to_colorgrid(pixel_obj.raw_data)
                if detect_raw_grid(grid_data):
                    return grid_data
            else:
                if isinstance(pixel_obj.raw_data, tuple) and len(pixel_obj.raw_data) == 2:
                    color, coords = pixel_obj.raw_data
                    if isinstance(color, int):
                        return [[color]]
        except:
            pass
    return None
    