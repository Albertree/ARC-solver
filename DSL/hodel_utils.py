
def totuple(nested_list):
    if isinstance(nested_list, list):
        return tuple(totuple(item) for item in nested_list)
    return nested_list

def togrid(data): # list of tuples [(color, (row, col))]
    # Step 1: Find the minimum and maximum row and column numbers
    min_row = min(data, key=lambda x: x[1][0])[1][0]
    max_row = max(data, key=lambda x: x[1][0])[1][0]
    min_col = min(data, key=lambda x: x[1][1])[1][1]
    max_col = max(data, key=lambda x: x[1][1])[1][1]

    # Calculate grid dimensions
    num_rows = max_row - min_row + 1
    num_cols = max_col - min_col + 1

    # Step 2: Initialize the grid with default value 13
    grid = [[12 for _ in range(num_cols)] for _ in range(num_rows)]

    # Step 3: Populate the grid with color_index
    for color_index, (row, col) in data:
        grid[row - min_row][col - min_col] = color_index

    return grid


# for print
def forprint(data):
    if len(data) < 2:
        print(data)
    for row in data:
        print(row)
    print()
    