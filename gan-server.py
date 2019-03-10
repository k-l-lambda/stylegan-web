
import io
import sys
import pickle
import numpy as np
import dnnlib
import dnnlib.tflib
import PIL.Image
from http.server import BaseHTTPRequestHandler, HTTPServer

import config



MODEL_URLS = {
	'ffhq':		'http://127.0.0.1/karras2019stylegan-ffhq-1024x1024.pkl',		# 9f4c085b663ed283f5853cc662bd0883
	'celebahq':	'http://127.0.0.1/karras2019stylegan-celebahq-1024x1024.pkl',	# 6604978f22ef7caea1ef5ca723282b43
	'bedrooms':	'http://127.0.0.1/karras2019stylegan-bedrooms-256x256.pkl',		# 2988bc55c7724955f2cdcc52002c1e1e
	'cars':		'http://127.0.0.1/karras2019stylegan-cars-512x384.pkl',			# 67373f1fa39fb6e5cfcae9da48223df2
	'cats':		'http://127.0.0.1/karras2019stylegan-cats-256x256.pkl',			# d09fc0938ea1aecf2af74ac0432e1279
}




class Handler(BaseHTTPRequestHandler):
	def handTest(self):
		global Gs
		#print('Gs:', Gs)

		rnd = np.random.RandomState(0)
		latents = rnd.randn(1, Gs.input_shape[1])

		# Generate image.
		fmt = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True)
		images = Gs.run(latents, None, truncation_psi = 0.7, randomize_noise = True, output_transform = fmt)

		# encode to PNG
		fp = io.BytesIO()
		PIL.Image.fromarray(images[0], 'RGB').save(fp, PIL.Image.registered_extensions()['.png'])

		self.send_response(200)
		self.end_headers()
		self.wfile.write(fp.getvalue())

	def do_GET(self):
		if self.path == '/test':
			self.handTest()
		else:
			self.send_response(404)
			self.end_headers()
			self.wfile.write(b'no handler for path: %s' % self.path.encode('ascii'))


def main(argv):
	#print('argv:', argv)

	model_name = argv[1] if len(argv) > 1 else'ffhq'
	model_url = MODEL_URLS.get(model_name)

	if not model_url:
		print('invalid model name:', model_name)
		return

	print('Initializing TensorFlow...')

	dnnlib.tflib.init_tf()

	print('Loading model %s ...' % model_name)

	with dnnlib.util.open_url(model_url, cache_dir = config.cache_dir) as f:
		global Gs
		_G, _D, Gs = pickle.load(f)

	try:
		server = HTTPServer(('0.0.0.0', config.server_port), Handler)

		print('gan server start on:', config.server_port)

		server.serve_forever()
	except:
		print('server interrupted:', sys.exc_info())


if __name__ == "__main__":
	main(sys.argv)
