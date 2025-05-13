import matplotlib.pyplot as plt
import numpy as np
import math
import cmath

ax = plt.figure().subplots()

def Circle(bend, x, y):
	radius = abs(1/bend)
	return ax.add_patch(plt.Circle([x,y],radius, fill = False))
	
def descartes(k1,k2,k3):
	KSum = k1 + k2 + k3
	KRoot = 2*math.sqrt(k1*k2 + k2*k3 + k1*k3)
	return KSum + KRoot
	
def complex_descartes(k1,k2,k3,k4,z1,z2,z3):
	KSum = z1*k1 + z2*k2 + z3*k3
	KRoot = 2*cmath.sqrt(z1*k1*z2*k2 + z2*k2*z3*k3 + z1*k1*z3*k3)
	return [(KSum + KRoot)/k4,(KSum - KRoot)/k4]

k1 = -1/200
k2 = 1/100
k3 = descartes(k1,k2,k2)
k4 = descartes(k2,k2,k3)
z1 = complex(200,200)
z2 = [complex(100,200),complex(300,200)]
z3 = complex_descartes(k1,k2,k2,k3,z1,z2[0],z2[1])
z4 = [complex_descartes(k2,k2,k3,k4,z2[0],z2[1],z3[1])[0],complex_descartes(k2,k2,k3,k4,z2[0],z2[1],z3[0])[0]]
print(z4)
Circle(k1, z1.real,z1.imag)
Circle(k2, z2[0].real,z2[0].imag)
Circle(k2, z2[1].real,z2[1].imag)
Circle(k3, z3[0].real,z3[0].imag)
Circle(k3, z3[1].real,z3[1].imag)
Circle(k4, z4[0].real,z4[0].imag)
Circle(k4, z4[1].real,z4[1].imag)

ax.set_xlim(0,400)
ax.set_ylim(0,400)
ax.axis("equal")
ax.axis("off")
plt.savefig("better circly thing", format='png', transparent=True)

plt.show()
