import matplotlib.pyplot as plt
import numpy as np
import math
import cmath

ax = plt.figure().subplots()

angle = 61.92*(math.pi/180)
rotation = complex(math.cos(angle),math.sin(angle))
negative = complex(math.cos(-angle),math.sin(-angle))

iterations = int(input("Iterations:"))

circles = [[-15,complex(200,200)],[32,complex(-1/15+1/32,0)*rotation+complex(200,200)],[32,complex(-1/15+1/32,0)*negative+complex(200,200)],[33,complex(1/15-1/33+200,200)]]
queue = [[circles[0],circles[1],circles[2]],[circles[0],circles[1],circles[3]],[circles[1],circles[2],circles[3]],[circles[0],circles[2],circles[3]]]

def good_circle(c,c1,c2,c3):
	if abs(c[1]-circles[0][1]) >= abs(1/circles[0][0]):
		print(abs(c[1]-circles[0][1]))
		return False
	return True

def Circle(c):
	bend = c[0]
	radius = abs(1/bend)
	return ax.add_patch(plt.Circle([c[1].real,c[1].imag],radius, fill = False))
	
def descartes(k1,k2,k3):
	KSum = k1 + k2 + k3
	KRoot = 2*math.sqrt(k1*k2 + k2*k3 + k1*k3)
	return KSum + KRoot
	
def complex_descartes(k1,k2,k3,k4,z1,z2,z3,sign):
	KSum = z1*k1 + z2*k2 + z3*k3
	KRoot = sign*2*cmath.sqrt(z1*k1*z2*k2 + z2*k2*z3*k3 + z1*k1*z3*k3)
	return (KSum + KRoot)/k4

for i in range(iterations):
	new_queue = []
	for triplet in queue:
		new = []
		[c1,c2,c3] = triplet
		new.append(descartes(c1[0],c2[0],c3[0]))
		new.append(complex_descartes(c1[0],c2[0],c3[0],new[0],c1[1],c2[1],c3[1],1))
		if good_circle(new,c1,c2,c3):
			circles.append(new)
			new_queue.append([c1,c2,circles[-1]])
			new_queue.append([c1,c3,circles[-1]])
			new_queue.append([c3,c2,circles[-1]])
		new = []
		[c1,c2,c3] = triplet
		new.append(descartes(c1[0],c2[0],c3[0]))
		new.append(complex_descartes(c1[0],c2[0],c3[0],new[0],c1[1],c2[1],c3[1],-1))
		if good_circle(new,c1,c2,c3):
			circles.append(new)
			new_queue.append([c1,c2,circles[-1]])
			new_queue.append([c1,c3,circles[-1]])
			new_queue.append([c3,c2,circles[-1]])
	queue = new_queue
	
print("Onto Plotting!")

for i in range(0,len(circles)):
	Circle(circles[i])
	print(i+1)

ax.set_xlim(199,201)
ax.set_ylim(199,201)
ax.axis("equal")
ax.axis("off")
plt.savefig("better circly thing.png", format='png', transparent=True)

plt.show()
