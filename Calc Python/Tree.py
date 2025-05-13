from math import *
import turtle

left = float(input("Left Angle:"))
right = float(input("Right Angle:"))
t = turtle.Turtle()
t.left(90)
stack = []

def branch(length, depth):
	if depth == 0: return
	t.forward(length)
	stack.append((t.pos(), t.heading()))
	t.left(left)
	branch(2/3*length, depth-1)
	(tp, current_angle) = stack.pop()
	t.setpos(tp)
	t.seth(current_angle)
	stack.append((t.pos(), t.heading()))
	t.right(right)
	branch(2/3*length, depth-1)
	(tp, current_angle) = stack.pop()
	t.setpos(tp)
	t.seth(current_angle)

branch(100,10)
