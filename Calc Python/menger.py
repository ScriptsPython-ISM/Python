import matplotlib.pyplot as plt

from random import randint
import math
import numpy


n = int(input("Number of Points:"))
iterations = int(input("Number of Iterations:"))
chaos = float(input("Chaos Denominator (must be >= numerator):"))
dem = float(input("Chaos Numerator:"))
pointsX = []
pointsY = []
pointsZ = []
pointX = []#20,20,20,30,40,40,40,30,20,20,20,30,40,40,40,30,20,20,40,40]
pointY = []#20,30,40,40,40,30,20,20,20,30,40,40,40,30,20,20,20,40,40,20]
pointZ = []#20,20,20,20,20,20,20,20,40,40,40,40,40,40,40,40,30,30,30,30]

for i in range(1, n + 1):
	pointX.append(float(input(f"Point X{i}:")))
	pointY.append(float(input(f"Point Y{i}:")))
	pointZ.append(float(input(f"Point Z{i}:")))

pointsX.append(float(input("\nStarting X:")))
pointsY.append(float(input("Starting Y:")))
pointsZ.append(float(input("Starting Z:")))

for i in range(0, iterations):
  m = randint(0, n-1)
  print(m)
  pointsX.append(pointsX[i]*(1-dem/chaos) + pointX[m]*dem/chaos)
  pointsY.append(pointsY[i]*(1-dem/chaos) + pointY[m]*dem/chaos)
  pointsZ.append(pointsZ[i]*(1-dem/chaos) + pointZ[m]*dem/chaos)

ax = plt.figure().add_subplot(projection = "3d")

ax.plot(pointX,pointY,pointZ, "go")
ax.scatter(pointsX, pointsY, pointsZ, s=1)

ax.axis("equal")

for angle in range(0, 360*4 + 1):
    angle_norm = (angle + 180) % 360 - 180

    elev = azim = roll = 0
    if angle <= 360:
        elev = angle_norm
    elif angle <= 360*2:
        azim = angle_norm
    elif angle <= 360*3:
        roll = angle_norm
    else:
        elev = azim = roll = angle_norm

    ax.view_init(elev, azim, roll)
    plt.title('Elevation: %d°, Azimuth: %d°, Roll: %d°' % (elev, azim, roll))

    plt.draw()
    plt.pause(.001)
