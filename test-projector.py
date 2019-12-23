
"""Test for StyleGAN2 projector."""

import pickle
import numpy as np
import PIL.Image
import dnnlib.tflib as tflib
import time

from projector import Projector
from training import misc



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

		print('t3:', time.time() - t0)

	with open('./models/vgg16_zhang_perceptual.pkl', 'rb') as f:
		lpips = pickle.load(f)

		print('t4:', time.time() - t0)

	#print('Gs:', Gs)
	proj = Projector()
	proj.set_network(Gs, lpips)

	image = PIL.Image.open('./images/seed0000-target.png')
	#image = image.resize((Di.input_shape[2], Di.input_shape[3]), PIL.Image.ANTIALIAS)
	image_array = np.array(image).swapaxes(0, 2).swapaxes(1, 2)
	image_array = misc.adjust_dynamic_range(image_array, [0, 255], [-1, 1])

	#pres = proj.run([image_array])
	#print('pres:', pres)

	print('t5:', time.time() - t0)

	proj.start([image_array])
	for step in proj.runSteps(1000):
		print('\rstep: %d' % step, end = '', flush = True)
		if step % 10 == 0:
			results = proj.get_images()
			#PIL.Image.fromarray(results[0].swapaxes(0, 2), 'RGB').save('./images/project-%d.png' % step)
			pilImage = misc.convert_to_pil_image(misc.create_image_grid(results), drange = [-1,1])
			pilImage.save('./images/project-%d.png' % step)

	print('t6:', time.time() - t0)

	dlatents = proj.get_dlatents()
	noises = proj.get_noises()
	print('dlatents:', dlatents.shape)
	print('noises:', len(noises), noises[0].shape, noises[-1].shape)


if __name__ == "__main__":
	main()
