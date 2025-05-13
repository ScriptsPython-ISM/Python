import ti_plotlib as plt
from random import random

def choice(l, p):
	chance = random()
	n = 0
	for i in range(len(p)):
		n+=p[i]
		if chance <= n:
			return l[i]

def function1(x,y):
	return (0.,0.16*y)
def function2(x,y):
	return (0.85*x + 0.04*y, -0.04*x + 0.85*y + 1.6)
def function3(x,y):
	return (0.2*x - 0.26*y, 0.23*x + 0.22*y + 1.6)
def function4(x,y):
	return (-0.15*x + 0.28*y, 0.26*x + 0.24*y + 0.44)
functions = [function1, function2, function3, function4]

plt.cls()
plt.window(-3,3,0,10)
plt.color(42, 120, 63)

points = int(input("Iterations:"))
x, y = 0, 0
plt.cls()
plt.window(-3,3,0,10)
for i in range(points):
	function = choice(functions, p=[0.01,0.85,0.07,0.07])
	x,y = function(x,y)
	plt.scatter([x],[y])

plt.show_plot()
