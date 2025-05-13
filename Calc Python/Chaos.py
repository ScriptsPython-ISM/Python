import ti_plotlib as plt
from random import randint
from math import *

rule = 0

def internalAngle(n):
  return ((n-2)*pi)/n

def optimal_r_num(N):
  n = floor(N/4)
  a = 0
  internal = internalAngle(N)
  for i in range(1,int(n)+1):
    a += cos(i*(pi-internal))
  return (1+2*a)
  
def optimal_r_den(N):
  n = floor(N/4)
  a = 0
  internal = internalAngle(N)
  for i in range(1,int(n)+1):
    a += cos(i*(pi-internal))
  return (2+2*a)

def create_polygonX(x, sides, distance):
  angle = 360/sides
  angle = angle * (pi / 180)
  create_pointsX = []
  for i in range(0,sides):
    create_pointsX.append(x + distance * cos(angle*i))
  return create_pointsX
  
def create_polygonY(y, sides, distance):
  angle = 360/sides
  angle = angle * (pi / 180)
  create_pointsY = []
  for i in range(0,sides):
    create_pointsY.append(y + distance * sin(angle*i))
  return create_pointsY

n = int(input("Number of Points:"))
iterations = int(input("Number of Iterations:"))
auto = input("Automatic Jump? (Y/N):")
if auto == "N":
  chaos = float(input("Chaos Denominator (must be >= numerator):"))
  dem = float(input("Chaos Numerator:"))
if auto == "Y":
  chaos = optimal_r_den(n)
  dem = optimal_r_num(n)
  
extra = input("Extra rules? (Y/N):")

if extra == "Y":
  print("\nA:No visiting same point twice in a row;\nB:No visiting points certain jump from previous;\nC:Only visit points certain jump from previous")
  rule = input("Select one of A, B and C:")
  if rule != "A":
    jump = int(input("What is that jump?"))

pointX = []
pointY = []
m = 0

auto = input("Automatic Shape? (Y/N):")
if auto == "N":
  for i in range(1, n + 1):
    pointX.append(float(input("Point X:")))
    pointY.append(float(input("Point Y:")))
if auto == "Y":
  pointX = create_polygonX(0, n, 20)
  pointY = create_polygonY(0, n, 20)

X=pointX[0]
Y=pointY[0]
plt.cls()
plt.window(min(pointY)*2,max(pointY)*2,min(pointX),max(pointX))


plt.color(0,0,255)

for i in range(0, iterations):
  previous = m
  m = -1
  if rule != "C":
    while (m == -1) or (rule == "A" and m == previous) or (rule == "B" and (((previous == n - jump ) and (m == previous - jump or m == 0)) or ((previous == 0) and (m == previous + jump or m == n - jump)) or (m == previous - jump or m == previous + jump))):
      m = randint(0, n - 1)
  else:
    m = randint(1,2)
    if m == 1:
      if not(previous<jump-1):
        m = previous - jump
      else:
        m = n - jump - 1
    elif m == 2:
      if previous > n-jump:
        m = previous + jump
      else:
        m = -1 + jump
  newX=X*(1-dem/chaos)+pointX[m]*dem/chaos
  newY=Y*(1-dem/chaos)+pointY[m]
  plt.scatter([newY], [newX])
  X=newX
  Y=newY

plt.show_plot()
