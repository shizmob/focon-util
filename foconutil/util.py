from struct import calcsize, unpack
from typing import Any


def take(data: bytes, n: int) -> tuple[bytes, bytes]:
	if len(data) < n:
		raise EOFError(f'not enough data to read {n} bytes')
	return data[:n], data[n:]

def take_unpack(data: bytes, fmt: str) -> tuple[tuple[Any, ...], bytes]:
	n = calcsize(fmt)
	b, data = take(data, n)
	return unpack(fmt, b), data
