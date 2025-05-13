def fibonacci(n: int) -> int:
	def fib_pair(k: int) -> tuple[int,int]:
		if k <= 1:
			return (k,1)
		fh, fh1 = fib_pair(k>>1)
		fk = fh * ((fh1<<1) - fh)
		fk1 = fh1**2 + fh**2
		if k & 1:
			fk, fk1 = fk1, fk+fk1
		return(fk, fk1)
	return fib_pair(n)[0]
