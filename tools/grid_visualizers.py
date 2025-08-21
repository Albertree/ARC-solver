def color_text(color_str):
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
    return rgb(*COLORS[int(color_str)])

def rgb(r, g, b):
    return f"\033[48;2;{r};{g};{b}m\033[38;2;{r};{g};{b}m{"  "}\033[0m"