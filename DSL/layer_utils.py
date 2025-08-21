def merge_layers(accumulated_layers, keep_original=False):
    merged_grid = [[13 for _ in range(90)] for _ in range(90)]
    for n, layer in enumerate(accumulated_layers[:-1]):
        for i in range(len(layer)):
            for j in range(len(layer[0])):
                if layer[i][j] != 13:
                    merged_grid[i][j] = layer[i][j]
    return merged_grid 