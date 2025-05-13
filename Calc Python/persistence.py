d = 1
maxi = 1
best = 0

def per(n, depth):
	digits = [int(i) for i in str(n)]
	result = 1
	for i in digits:
		result*=i
	if len(str(result))!=1:
		depth = per(result, depth+1)
	return depth

for i in range(1, int(input("Max:"))):
	per(i,d)
	if d>maxi:
		maxi = d
		best = i
		print(best)
print(best)
