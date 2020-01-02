
import base64
import struct
import math
import numpy as np



def encodeFloat32(latents):
	return base64.b64encode(struct.pack('f' * latents.shape[0], *latents))


def decodeFloat32(code, len = 512):
	return np.array(struct.unpack('f' * len, base64.b64decode(code)))


def encodeFixed16(latents):
	intLatents = list(map(lambda x: min(max(math.floor(x * 1024), -0x8000), 0x7fff), latents))
	return base64.b64encode(struct.pack('h' * latents.shape[0], *intLatents))


def decodeFixed16(code, len = 512):
	intLatents = np.array(struct.unpack('h' * len, base64.b64decode(code)))
	return np.array(list(map(lambda x: x / 1024, intLatents)))
