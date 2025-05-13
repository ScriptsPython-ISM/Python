import math

def create_polygon(x, y, sides, distance):
	angle = 360/sides
	angle = angle * (math.pi / 180)
	pointsX = []
	pointsY = []
	for i in range(0,sides):
		pointsX.append(x + distance * math.cos(angle*i))
		pointsY.append(y + distance * math.sin(angle*i))
	return pointsX, pointsY
