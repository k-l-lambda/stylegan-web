
import io
import os
import sys
import time
import pickle
import json
import base64
import struct
import numpy as np
import PIL.Image
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import cgi

import dnnlib
import dnnlib.tflib

import config



MODEL_URLS = {
	'ffhq':		'http://127.0.0.1/karras2019stylegan-ffhq-1024x1024.pkl',		# 9f4c085b663ed283f5853cc662bd0883
	'celebahq':	'http://127.0.0.1/karras2019stylegan-celebahq-1024x1024.pkl',	# 6604978f22ef7caea1ef5ca723282b43
	'bedrooms':	'http://127.0.0.1/karras2019stylegan-bedrooms-256x256.pkl',		# 2988bc55c7724955f2cdcc52002c1e1e
	'cars':		'http://127.0.0.1/karras2019stylegan-cars-512x384.pkl',			# 67373f1fa39fb6e5cfcae9da48223df2
	'cats':		'http://127.0.0.1/karras2019stylegan-cats-256x256.pkl',			# d09fc0938ea1aecf2af74ac0432e1279
}


MIME_TYPES = {
	'.html': 'text/html',
	'.js': 'application/javascript',
}



class Handler(BaseHTTPRequestHandler):
	def handTest(self):
		queries = parse_qs(urlparse(self.path).query, keep_blank_values = True)

		global Gs, Gi

		model = Gi if queries.get('instantaneous') else Gs
		seed = int(queries.get('seed', [0])[0])

		rnd = np.random.RandomState(seed)
		latents = rnd.randn(1, model.input_shape[1])

		t0 = time.time()

		# Generate image.
		fmt = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True)
		images = model.run(latents, None, truncation_psi = 0.7, randomize_noise = True, output_transform = fmt)

		print('test time cost:', time.time() - t0)

		# encode to PNG
		fp = io.BytesIO()
		PIL.Image.fromarray(images[0], 'RGB').save(fp, PIL.Image.registered_extensions()['.png'])

		self.send_response(200)
		self.end_headers()
		self.wfile.write(fp.getvalue())


	def handGenerate(self):
		queries = parse_qs(urlparse(self.path).query, keep_blank_values = True)

		global Gs, Gi

		model = Gi if queries.get('instantaneous') else Gs

		latent_len = model.input_shape[1]
		latents = np.array(struct.unpack('f' * latent_len, base64.b64decode(queries.get('latents')[0]))).reshape([1, latent_len])

		truncation_psi = float(queries.get('psi', [0.7])[0])
		randomize_noise = False if queries.get('no_rnd_noise') else True

		t0 = time.time()

		# Generate image.
		fmt = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True)
		images = model.run(latents, None, truncation_psi = truncation_psi, randomize_noise = randomize_noise, output_transform = fmt)

		print('test time cost:', time.time() - t0)

		# encode to PNG
		fp = io.BytesIO()
		PIL.Image.fromarray(images[0], 'RGB').save(fp, PIL.Image.registered_extensions()['.png'])

		self.send_response(200)
		self.end_headers()
		self.wfile.write(fp.getvalue())


	def handDiscriminate(self):
		global Di

		ctype, pdict = cgi.parse_header(self.headers.get('Content-Type'))
		pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
		vars = cgi.parse_multipart(self.rfile, pdict)
		#print('handDiscriminate:', vars.get('image')[0])
		#image = PIL.Image.frombytes(data = vars.get('image')[0], decoder_name = 'png')
		stream = io.BytesIO(vars.get('image')[0])
		image = PIL.Image.open(stream)
		#print('handDiscriminate:', image)
		image_array = np.array(image)
		#print('image shape:', image_array.shape, Di.num_inputs, Gs.num_inputs, Di.input_shape)
		result = Di.run(image_array.reshape([1, 3, 1024, 1024]), None)
		print('handDiscriminate:', result)

		self.send_response(200)
		self.end_headers()
		self.wfile.write(str(result[0][0]).encode('utf-8'))


	def do_GET(self):
		url = urlparse(self.path)

		if url.path == '/test':
			self.handTest()
			return
		elif url.path == '/generate':
			return self.handGenerate()
		elif url.path == '/spec':
			global model_name
			global Gs

			self.send_response(200)
			self.send_header('Content-type', 'application/json')
			self.end_headers()
			self.wfile.write(json.dumps({
				'model': model_name,
				'latents_dimensions': Gs.input_shape[1],
			}).encode('ascii'))

			return
		elif url.path == '/':
			self.path = '/index.html'

		# static files
		filename = os.path.join(os.curdir, './dist', self.path[1:])
		print('filename:', filename)

		if os.path.isfile(filename):
			ext = os.path.splitext(filename)[1]

			self.send_response(200)
			self.send_header('Content-type', MIME_TYPES.get(ext, 'text/plain'))
			self.end_headers()
			self.wfile.write(open(filename, 'rb').read())
		else:
			self.send_response(404)
			self.end_headers()
			self.wfile.write(b'no handler for path: %s' % self.path.encode('ascii'))


	def do_POST(self):
		url = urlparse(self.path)

		if url.path == '/discriminate':
			return self.handDiscriminate()


def main(argv):
	#print('argv:', argv)
	global model_name

	model_name = argv[1] if len(argv) > 1 else'ffhq'
	model_url = MODEL_URLS.get(model_name)

	if not model_url:
		print('invalid model name:', model_name)
		return

	print('Initializing TensorFlow...')

	dnnlib.tflib.init_tf()

	print('Loading model %s ...' % model_name)

	with dnnlib.util.open_url(model_url, cache_dir = config.cache_dir) as f:
		global Gs, Gi, Di
		Gi, Di, Gs = pickle.load(f)
		#print('models i:', Gi.input_shape, Di.input_shape)		[, 512]					[, 3, 1024, 1024]
		#print('models o:', Gi.output_shape, Di.output_shape)	[, 3, 1024, 1024]		[, 1]

	try:
		server = HTTPServer(('0.0.0.0', config.server_port), Handler)

		print('gan server start on:', config.server_port)

		server.serve_forever()
	except:
		print('server interrupted:', sys.exc_info())



if __name__ == "__main__":
	main(sys.argv)
