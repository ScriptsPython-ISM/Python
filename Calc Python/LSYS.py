import ti_plotlib as plt
from math import *

def simulate_bounds(axiom, rules, angle, distance, depth):
    stack = []
    x, y = 0, 0
    angle_deg = 0
    min_x = max_x = x
    min_y = max_y = y

    def interpret(symbol, d):
        nonlocal x, y, angle_deg, min_x, max_x, min_y, max_y
        if d == 0:
            if symbol == 'F':
                new_x = x + distance * cos(radians(angle_deg))
                new_y = y + distance * sin(radians(angle_deg))
                x, y = new_x, new_y
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
            elif symbol == '+':
                angle_deg += angle
            elif symbol == '-':
                angle_deg -= angle
            elif symbol == '[':
                stack.append((x, y, angle_deg))
            elif symbol == ']':
                x, y, angle_deg = stack.pop()
        else:
            replacement = rules.get(symbol, symbol)
            for ch in replacement:
                interpret(ch, d - 1)

    for ch in axiom:
        interpret(ch, depth)

    return min_x, max_x, min_y, max_y

def draw_lsystem(axiom, rules, angle, distance, depth):
    stack = []
    x, y = 0, 0
    angle_deg = 0

    def interpret(symbol, d):
        nonlocal x, y, angle_deg
        if d == 0:
            if symbol == 'F':
                new_x = x + distance * cos(radians(angle_deg))
                new_y = y + distance * sin(radians(angle_deg))
                plt.line(x, y, new_x, new_y)
                x, y = new_x, new_y
            elif symbol == '+':
                angle_deg += angle
            elif symbol == '-':
                angle_deg -= angle
            elif symbol == '[':
                stack.append((x, y, angle_deg))
            elif symbol == ']':
                x, y, angle_deg = stack.pop()
        else:
            replacement = rules.get(symbol, symbol)
            for ch in replacement:
                interpret(ch, d - 1)

    for ch in axiom:
        interpret(ch, depth)

print("For a Koch Curve or Terdragon: Axiom = F")
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
rules = eval(input("Rules:"))

n_iterations = int(input("Iterations:"))
angle = int(input("Angle of Turn:"))
distance = 1

min_x, max_x, min_y, max_y = simulate_bounds(axiom, rules, angle, distance, n_iterations)

plt.cls()
plt.color(0, 0, 0)
plt.window(min_x, max_x, min_y, max_y)

draw_lsystem(axiom, rules, angle, distance, n_iterations)
plt.show_plot()
