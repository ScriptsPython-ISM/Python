import matplotlib.pyplot as plt
from random import randint

size = int(input("Size of area to walk:"))

start = (0, 0)
visited = set()
visited.add(start)

stack = [start]

walls = set()

for x in range(size + 1):
    for y in range(size + 1):
        if x < size:
            walls.add(((x, y), (x + 1, y))) 
        if y < size:
            walls.add(((x, y), (x, y + 1))) 

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

        wall = tuple(sorted([current, next_pos]))
        if wall in walls:
            walls.remove(wall)
    else:
        stack.pop()

for (x1, y1), (x2, y2) in walls:
    plt.plot((x1, x2), (y1, y2), 'k')

plt.plot((-1,size+1,size+1,-1,-1),(-1,-1,size+1,size+1,-1))

plt.axis('equal')
plt.axis('off')
plt.show()
