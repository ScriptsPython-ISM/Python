import matplotlib.pyplot as plt
import numpy as np
import ast

def l_system_dragon_curve(n_iterations):
	print("For a Koch Curve or a Terdragon: F")
	print("For a Dragon Curve: FX")
	print("For a Twindragon: FX+FX+")
	print("For a Plant: X")
	print("For a Hilbert Curve: A")
	axiom = input("Axiom:")
	print("For a Koch Curve: {'F':'F+F--F+F'}")
	print("For a Dragon Curve: {'X':'X+YF+', 'Y':'-FX-Y'}")
	print("For a Twindragon: {'X':'X+YF','Y':'FX-Y'}")
	print("For a Terdragon: {'F':'F+F-F'}")
	print("For a Plant: {'X':'F+[[X]-X]-F[-FX]+X','F':'FF'}")
	print("For a Hilbert Curve: {'A':'-BF+AFA+FB-', 'B':'+AF-BFB-FA+'}")
	rules = ast.literal_eval(input("Rules:"))
	for _ in range(n_iterations):
		axiom = ''.join(rules.get(c, c) for c in axiom)
	return axiom

def turtle_draw_dragon_curve(sentence, angle, distance):
    stack = []
    x, y = 0, 0
    angle_deg = 0
    points = [(x, y)]
    for command in sentence:
        if command == 'F':
            x += distance * np.cos(np.radians(angle_deg))
            y += distance * np.sin(np.radians(angle_deg))
            points.append((x, y))
        elif command == '+':
            angle_deg += angle
        elif command == '-':
            angle_deg -= angle
        elif command == '[':
            stack.append((x, y, angle_deg))
        elif command == ']':
            x, y, angle_deg = stack.pop()
            points.append((x, y))
    return points

n_iterations = int(input("Iterations:"))
angle = int(input("Angle of Turn:"))
distance = 1

sentence = l_system_dragon_curve(n_iterations)

points = turtle_draw_dragon_curve(sentence, angle, distance)

plt.figure(figsize=(10, 10))
plt.plot(*zip(*points), color='black')
plt.axis('equal')
plt.axis('off')
plt.show()
