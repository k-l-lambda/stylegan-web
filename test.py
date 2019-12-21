
"""Minimal script for generating an image using pre-trained StyleGAN2 generator."""

import pickle
import numpy as np
import PIL.Image
import dnnlib.tflib as tflib
import time



def main():
	t0 = time.time()
	print('t0:', t0)

	# Initialize TensorFlow.
	tflib.init_tf()	 # 0.82s

	print('t1:', time.time() - t0)

	# Load pre-trained network.
	with open('./models/stylegan2-ffhq-config-f.pkl', 'rb') as f:
		#print('f:', f)
		print('t2:', time.time() - t0)

		_G, _D, Gs = pickle.load(f)	 # 13.09s
		# _G = Instantaneous snapshot of the generator. Mainly useful for resuming a previous training run.
		# _D = Instantaneous snapshot of the discriminator. Mainly useful for resuming a previous training run.
		# Gs = Long-term average of the generator. Yields higher-quality results than the instantaneous snapshot.

		print('t3:', time.time() - t0)

	# Print network details.
	#Gs.print_layers()

	print('t4:', time.time() - t0)

	# Pick latent vector.
	rnd = np.random.RandomState(4)
	latents = rnd.randn(1, Gs.input_shape[1])

	print('t5:', time.time() - t0)

	print('input_shape:', Gs.input_shape)
	#print('latents:', latents)

	# Generate image.
	fmt = dict(func=tflib.convert_images_to_uint8, nchw_to_nhwc=True)	   # 0.00s
	print('t6:', time.time() - t0)
	images = Gs.run(latents, None, truncation_psi=-0.5, randomize_noise=True, output_transform=fmt)	 # 6.95s

	print('images:', images)

	print('t7:', time.time() - t0)

	# Save image.
	PIL.Image.fromarray(images[0], 'RGB').save('./example.png')		# 0.60s

	print('t8:', time.time() - t0)

if __name__ == "__main__":
	main()
