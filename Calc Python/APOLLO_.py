import turtle
from math import *
from random import random

angle = radians(61.92)
rotation = complex(cos(angle), sin(angle))
negative = complex(cos(-angle), sin(-angle))

iterations = int(input("Iterations: "))



pen = turtle.Turtle()
#pen.hideturtle()
pen.penup()
#pen.hidegrid()

import math

def complex_sqrt_parts(E, sign):
	a = E.real
	b = E.imag
	r = math.sqrt(a*a+b*b)
	real_part = sign * 2 * math.sqrt((r + a) / 2)
	
	if b > 0:
		b_sign = 1
	elif b < 0:
		b_sign = -1
	else:
		b_sign = 0

	imag_part = sign * 2 * b_sign * math.sqrt((r - a) / 2)

	return complex(real_part,imag_part)

def good(c,other1,other2,other3):
	cs = [other1,other2,other3]
	if c0 in cs:
		cs.remove(c0)
	if abs(c[1] - c0[1]) >= abs(1 / c0[0]):
		return False
	for other in cs:
		print(abs(c[1]-other[1])-0.1, 1/c[0]+1/other[0], abs(c[1]-other[1])+0.1)
		if  not(abs(c[1]-other[1])-1 <= 1/c[0]+1/other[0] <= abs(c[1]-other[1])+1):
			return False
	return True

def recurse(c1, c2, c3, depth):
	if depth == 0:
		return 
	for sign in [1,-1]:
		k4 = descartes(c1[0], c2[0], c3[0])
		z4 = complex_descartes(c1[0], c2[0], c3[0], k4, c1[1], c2[1], c3[1], sign)
		new_circle = (k4, z4)
		if good(new_circle, c1, c2, c3):
			draw_circle(new_circle)
			recurse(c1, c2, new_circle, depth - 1)
			recurse(c1, c3, new_circle, depth - 1)
			recurse(c2, c3, new_circle, depth - 1)

def draw_circle(c):
	bend = c[0]
	radius = 10*abs(1 / bend)
	center = 10*c[1]
	pen.goto(center.real, center.imag - radius)
	pen.setheading(0)
	pen.pendown()
	pen.circle(radius)
	pen.penup()

def descartes(k1, k2, k3):
	KSum = k1 + k2 + k3
	KRoot = 2 * pow(abs(k1*k2 + k2*k3 + k1*k3),1/2)
	return KSum + KRoot

def complex_descartes(k1, k2, k3, k4, z1, z2, z3, sign):
	KSum = z1 * k1 + z2 * k2 + z3 * k3
	E=z1*k1*z2*k2+z2*k2*z3*k3+z1*k1*z3*k3
	KRoot = sign*2*E**.5
	return (KSum + KRoot) / k4

k0 = -15/300
ratio = random()*(abs(1/k0))
k1 = 1/ratio
k2 = 1/(1/abs(k0)-1/k1)

z0 = complex(0, 0)

midpoint = (z0.real + (1/abs(k0)) - (((1/k1)/(1/abs(k0)))*2/abs(k0)))

z1 = complex(midpoint + 1/k1, 0)
z2 = complex(midpoint - 1/k2, 0)

c0 = (k0, z0)
c1 = (k1, z1)
c2 = (k2, z2)

#c0 = (-15/300, complex(0, 0))
#c1 = (32/300, complex(-300/15+300/32, 0) * rotation)
#c2 = (32/300, complex(-300/15+300/32, 0) * negative)
#c3 = (33/300, complex(300/15 - 300/33,0))

for c in [c0, c1, c2]:
	draw_circle(c)

recurse(c0, c1, c2, iterations+1)
pen.done()
