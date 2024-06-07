from typing import Any, Sequence

def batched(arr: Sequence[Any], batch_size: int = 10000):
	n = 0
	while n*batch_size < len(arr):
		yield arr[n*batch_size : (n+1)*batch_size]
		n += 1
