
"""Test for StyleGAN2 projector."""

import pickle
import numpy as np
import PIL.Image
import dnnlib.tflib as tflib
import time

from projector import Projector



def main():
	t0 = time.time()
	print('t0:', t0)

	# Initialize TensorFlow.
	tflib.init_tf()	 # 0.82s

	print('t1:', time.time() - t0)

	# Load pre-trained network.
	with open('./models/stylegan2-car-config-f.pkl', 'rb') as f:
		#print('f:', f)
		print('t2:', time.time() - t0)

		_G, _D, Gs = pickle.load(f)	 # 13.09s
		# _G = Instantaneous snapshot of the generator. Mainly useful for resuming a previous training run.
		# _D = Instantaneous snapshot of the discriminator. Mainly useful for resuming a previous training run.
		# Gs = Long-term average of the generator. Yields higher-quality results than the instantaneous snapshot.

		print('t3:', time.time() - t0)

	with open('./models/vgg16_zhang_perceptual.pkl', 'rb') as f:
		lpips = pickle.load(f)

		print('t4:', time.time() - t0)

	#print('Gs:', Gs)
	proj = Projector()
	proj.set_network(Gs, lpips)

	image = PIL.Image.open('./images/seed0001-target.png')
	#image = image.resize((Di.input_shape[2], Di.input_shape[3]), PIL.Image.ANTIALIAS)
	image_array = np.array(image).swapaxes(0, 2)
	#image_array = np.pad(np.array(image), ((0, 0), (0, 0), (0, 1)), 'constant', constant_values = (1, 1))

	#print('image:', image)

	pres = proj.run([image_array])
	print('pres:', pres)


if __name__ == "__main__":
	main()
