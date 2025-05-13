import matplotlib.pyplot as plt
import numpy as np

def function1(x,y):
	return (0.,0.16*y)
def function2(x,y):
	return (0.85*x + 0.04*y, -0.04*x + 0.85*y + 1.6)
def function3(x,y):
	return (0.2*x - 0.26*y, 0.23*x + 0.22*y + 1.6)
def function4(x,y):
	return (-0.15*x + 0.28*y, 0.26*x + 0.24*y + 0.44)
functions = [function1, function2, function3, function4]

points = int(input("Iterations:"))
x, y = 0, 0
x_list = []
y_list = []
for i in range(points):
	function = np.random.choice(functions, p=[0.01,0.85,0.07,0.07])
	x, y = function(x,y)
	x_list.append(x)
	y_list.append(y)

plt.scatter(x_list,y_list, s = 0.1)
plt.axis('off')
export = input("Export (Y/N):")
if export == "Y":
	plt.savefig(input("As:"), format='png', transparent=True)

plt.show()
