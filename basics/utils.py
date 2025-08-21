def rgb(r, g, b, text):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

def rgb_bg(r, g, b, text):
    # Set both background and foreground (text) to the same color
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{r};{g};{b}m{text}\033[0m"

def color_text(index, text):
    # Define colors as a constant dictionary
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
    # Use the same color for both background and text
    r, g, b = COLORS.get(index, (255, 255, 255)) # Default to white for unknown colors
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{r};{g};{b}m{text}\033[0m"

def printcg(grids, titles=None, wait_for_enter=True):
    """
    Print one or more colored grids side-by-side in the terminal.
    
    Args:
        grids: A list of 2D arrays/lists of color indices.
        titles: A list of titles for each grid.
        wait_for_enter: If True, wait for Enter key before returning.
    """
    # If a single grid is passed, wrap it in a list for consistent handling
    if grids and isinstance(grids[0], list) and (not grids[0] or isinstance(grids[0][0], int)):
        grids = [grids]

    print("\033[2J\033[H", end='')  # Clear screen and move to home

    grid_widths = [len(grid[0]) * 2 if grid and grid[0] else 0 for grid in grids]

    # Print titles
    if titles:
        title_line = ""
        for i, title in enumerate(titles):
            padding = (grid_widths[i] - len(title)) // 2
            padding = max(0, padding)
            title_line += f"{' ' * padding}{title}{' ' * (grid_widths[i] - len(title) - padding)}    "
        print(title_line)
        print()

    max_height = max(len(grid) for grid in grids if grid) if grids else 0

    for i in range(max_height):
        row_segments = []
        for j, grid in enumerate(grids):
            if i < len(grid):
                row_str = ''.join(color_text(val, "  ") for val in grid[i])
                row_segments.append(f"{row_str}{' ' * (grid_widths[j] - len(grid[i]) * 2)}")
            else:
                row_segments.append(" " * grid_widths[j])
        print("    ".join(row_segments))
    
    if wait_for_enter:
        print("\nPress Enter to continue...", end='')
        input()




    