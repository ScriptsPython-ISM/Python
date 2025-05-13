import ti_draw as draw
import time
import random

# Grid dimensions (smaller size for performance)
rows = 9
cols = 12
cell_size = min(320 / cols, 240 / rows)

# === INIT GRID ===

def rand_row(cols):
    s = ""
    for _ in range(cols):
        s += '1' if random.randint(0, 4) == 0 else '0'
    return s

# Create one string per row (still manageable memory size)
grid = [rand_row(cols) for _ in range(rows)]

# === UTILITIES ===

# Get cell value with wrapping
def get(grid, x, y):
    x %= rows
    y %= cols
    return grid[x][y]

# Count live neighbors with wrapping
def count_neighbors(grid, x, y):
    count = 0
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            if get(grid, x + dx, y + dy) == '1':
                count += 1
    return count

# Generate next generation grid and changes list
def next_gen(grid):
    new_grid = []
    changes = []
    for x in range(rows):
        new_row = ""
        for y in range(cols):
            cell = grid[x][y]
            n = count_neighbors(grid, x, y)
            if cell == '1' and n in (2, 3):
                new_row += '1'
            elif cell == '0' and n == 3:
                new_row += '1'
            else:
                new_row += '0'
            if cell != new_row[-1]:
                changes.append((x, y, new_row[-1]))  # Only track changed cells
        new_grid.append(new_row)
    return new_grid, changes

# Batch draw only changed cells (faster performance)
def draw_changes(changes):
    for x, y, state in changes:
        px = y * cell_size
        py = x * cell_size
        if state == '1':
            draw.fill_rect(px, py, px + cell_size - 1, py + cell_size - 1)
        else:
            draw.clear_rect(px, py, px + cell_size - 1, py + cell_size - 1)

# === MAIN LOOP ===
# Initial drawing of the grid
draw.clear()
for x in range(rows):
    for y in range(cols):
        if grid[x][y] == '1':
            px = y * cell_size
            py = x * cell_size
            draw.fill_rect(px, py, px + cell_size - 1, py + cell_size - 1)

# Main loop
while True:
    grid, changes = next_gen(grid)
    draw_changes(changes)
    time.sleep(0.1)
