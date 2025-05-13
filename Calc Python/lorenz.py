import matplotlib.pyplot as plt

ax = plt.figure().add_subplot(projection = "3d")
plt.axis("equal")

x = 0.01
y = 0.01
z = 0.01
ox = 0.01
oy = 0.01
oz = 0.01
a = eval(input("A:"))
b = eval(input("B:"))
c = eval(input("C:"))
dt = 0.01

for j in range(10):
	x, y, z = ox, oy, oz
	for i in range(int(input("Iterations:"))):
		dx = (-y - z)*dt
		dy = (x + a*y)*dt
		dz = (b + z*(x - c))*dt
		plt.plot([x,x+dx],[y,y+dy],[z,z+dz],'b-')
		x+=dx
		y+=dy
		z+=dz
	ox += 0.01
	oy += 0.01
	oz += 0.01

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
    
plt.show()
