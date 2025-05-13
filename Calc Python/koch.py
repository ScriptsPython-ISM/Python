import matplotlib.pyplot as plt
import numpy as np

def l_system(axiom, rules, n_iterations):
    for _ in range(n_iterations):
        axiom = ''.join(rules.get(c, c) for c in axiom)
    return axiom

def turtle_draw(sentence, angle, distance):
    stack = []
    x, y = 0, 0
    points = [(x, y)]
    for command in sentence:
        if command == 'F':
            x += distance * np.cos(angle)
            y += distance * np.sin(angle)
            points.append((x, y))
        elif command == '+':
            angle += np.radians(turn)
        elif command == '-':
            angle -= np.radians(turn)
        elif command == '[':
            stack.append((x, y, angle))
        elif command == ']':
            x, y, angle = stack.pop()
            points.append((x, y))
    return points

axiom = input("Axiom:")
rules = {'F': 'F+F−F−F+F'}
n_iterations = int(input("Iterations:"))
turn = int(input("Angle of Turn:"))
angle = 0
distance = 1

sentence = l_system(axiom, rules, n_iterations)

points = turtle_draw(sentence, angle, distance)

plt.figure(figsize=(10, 10))
plt.plot(*zip(*points), color='black')
plt.axis('equal')
plt.axis('off')
plt.show()
