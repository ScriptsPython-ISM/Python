import matplotlib.pyplot as plt
import sympy

def rotate(x, y, cx, cy, theta):
	translated_x = x# - cx
	translated_y = y# - cy
	rotated_x = translated_x * sympy.cos(theta) - translated_y * sympy.sin(theta)
	rotated_y = translated_x * sympy.sin(theta) + translated_y * sympy.cos(theta)
	return [rotated_x+cx,rotated_y+cy]

angle = float(input("Rotation (degrees):"))*(sympy.pi/180)
iterations = int(input("Iterations:"))

pointsX = [0,1]
pointsY = [0,0]
y_centre = 0
x_centre = 0

pointsX.append(rotate(pointsX[1],pointsY[1], 0, 0, angle)[0]+1)
pointsY.append(rotate(pointsX[1],pointsY[1], 0, 0, angle)[1])
print(pointsX)
print(pointsY)
print(angle*(180/sympy.pi))

for i in range(0,iterations):
	n = int(len(pointsX)-1)
	for j in range(0,n):
		new_x = rotate(pointsX[j],pointsY[j], pointsX[n], pointsY[n], angle)[0]
		new_y = rotate(pointsX[j],pointsY[j], pointsX[n], pointsY[n], angle)[1]
		pointsX.append(new_x)
		pointsY.append(new_y)

plt.plot(pointsX,pointsY,linewidth = 0.1)

#plt.plot(pointsX,pointsY,"go")

plt.axis("equal")

plt.show()
