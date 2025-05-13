import math
import numpy

pi = math.pi

def internalAngle(n):
	return ((n-2)*pi)/n

N = int(input("Number of Sides:"))
wesh, n = numpy.modf(N/4)
a = 0
internal = internalAngle(N)
for i in range(1,int(n)+1):
	a += math.cos(i*(pi-internal))
	
print((1+2*a),(2+2*a))
