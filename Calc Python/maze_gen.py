import ti_plotlib as plt
from random import randint
import time

size = int(input("Size of area to walk:"))

start = (0, 0)
visited = set()
visited.add(start)

stack = [start]

def get_randomized_neighbors(x, y):
    directions = [(1,0), (-1,0), (0,1), (0,-1)]
    result = []
    picked = []

    while len(picked) < 4:
        i = randint(0, 3)
        if i not in picked:
            picked.append(i)
            dx, dy = directions[i]
            nx, ny = x + dx, y + dy
            if 0 <= nx <= size and 0 <= ny <= size and (nx, ny) not in visited:
                result.append((nx, ny))
    return result

while stack and len(visited) < (size + 1) * (size + 1):
    current = stack[-1]
    neighbors = get_randomized_neighbors(*current)

    if neighbors:
        next_pos = neighbors[0]
        visited.add(next_pos)
        stack.append(next_pos)
        plt.line(current[0],next_pos[0], current[1], next_pos[1], 'b')
        plt.draw()
    else:
        stack.pop()

plt.show_plot()
