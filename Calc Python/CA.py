from ti_draw import *
from random import randint

y = 0

def newState(left,state,right):
	neighbourhood = [int(left),int(state),int(right)]
	new_state = state
	if neighbourhood == [1,1,1]:
		new_state = int(rule[0])
	if neighbourhood == [1,1,0 ]:
		new_state = int(rule[1])
	if neighbourhood == [1,0,1]:
		new_state = int(rule[2])
	if neighbourhood == [1,0,0]:
		new_state = int(rule[3])
	if neighbourhood == [0,1,1]:
		new_state = int(rule[4])
	if neighbourhood == [0,1,0]:
		new_state = int(rule[5])
	if neighbourhood == [0,0,1]:
		new_state = int(rule[6])
	if neighbourhood == [0,0,0]:
		new_state = int(rule[7])
	return new_state

iterations = int(input("Iterations:"))

rule = str(bin(int(input("Rule:"))))
ca = []
new_ca = []
for i in range(0,int(input("Width (must be odd):"))):
	ca.append(0)
ca[int((len(ca))/2)] = 1
rule = list(rule)
del rule[0]
del rule[0]
for i in range(0,8-len(rule)):
	rule.insert(0,'0')
for i in range(1,iterations):
	new_ca = []
	for j in range(0,len(ca)):
		left = ca[j-1]
		state = ca[j]
		if j != len(ca)-1:
			right = ca[j+1]
		else:
			right = ca[0]
		if state == 1:
			fill_rect([j,y],1,1)
		new_ca.append(newState(left,state,right))
	ca = new_ca
	y-=1
set_window(0,len(ca),y,1)
if [0,0,1] == [0,0,1]:
	plt.show()
