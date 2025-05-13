import matplotlib.pyplot as plt
import matplotlib.animation as animation

N = 500

def load_grid_from_file(filename):
    grid = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        if len(lines) != N:
            raise ValueError("Grid must have exactly {N} lines.")
        for i, line in enumerate(lines):
            row = []
            line = line.strip()
            if len(line) != N:
                raise ValueError(f"Line {i+1} must have exactly {N} characters.")
            for char in line:
                row.append(1 if char == '1' else 0)
            grid.append(row)
    return grid

def count_neighbors(grid, x, y):
    total = 0
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx = (x + dx) % N
            ny = (y + dy) % N
            total += grid[nx][ny]
    return total

def update(frameNum, img, grid):
    newGrid = [[0]*N for _ in range(N)]
    for i in range(N):
        for j in range(N):
            neighbors = count_neighbors(grid, i, j)
            if grid[i][j] == 1:
                newGrid[i][j] = 1 if 2 <= neighbors <= 3 else 0
            else:
                newGrid[i][j] = 1 if neighbors == 3 else 0
    for i in range(N):
        for j in range(N):
            grid[i][j] = newGrid[i][j]
    img.set_data(grid)
    return img,

grid = load_grid_from_file("start.txt")

fig, ax = plt.subplots()
img = ax.imshow(grid, interpolation='nearest', cmap='gray_r')
ani = animation.FuncAnimation(fig, update, fargs=(img, grid), frames=100, interval=300, save_count=50)

plt.axis('off')
plt.show()
