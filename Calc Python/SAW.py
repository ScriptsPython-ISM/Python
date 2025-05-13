import matplotlib.pyplot as plt
from random import randint

size = int(input("Size of are to walk:"))
iterations = int(input("Iterations:"))

start = (0, 0)
visited = set()
visited.add(start)

pointX = [start[0]]
pointY = [start[1]]

for i in range(iterations):
    counted = 0
    new_x, new_y = None, None

    while counted < iterations:
        direction = randint(1, 4)
        x, y = pointX[-1], pointY[-1]

        if direction == 1:  
            new_x, new_y = x + 1, y
        elif direction == 2:  
            new_x, new_y = x - 1, y
        elif direction == 3:  
            new_x, new_y = x, y + 1
        elif direction == 4:  
            new_x, new_y = x, y - 1

        if (0 <= new_x <= size) and (0 <= new_y <= size) and ((new_x, new_y) not in visited):
            break 

        counted += 1

    if counted < iterations:
        pointX.append(new_x)
        pointY.append(new_y)
        visited.add((new_x, new_y))

plt.plot(pointX, pointY)
plt.title("Self-Avoiding Walk")
plt.axis("equal")
plt.show()
