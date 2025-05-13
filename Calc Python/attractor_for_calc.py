import ti_plotlib as plt

x = 0.01
y = 0.01
z = 0.01
a = eval(input("A:"))
b = eval(input("B:"))
c = eval(input("C:"))
dt = 0.01

while True:
	dx = (a * (y - x))*dt
	dy = (x * (b - z) - y)*dt
	dz = (x * y - c * z)*dt
	plt.plot([x,x+dx],[y,y+dy],'b-')
	x+=dx
	y+=dy
	z+=dz
