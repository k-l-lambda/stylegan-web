
import os
import sys
import io
import time
from dotenv import load_dotenv
import flask
import pickle
import PIL.Image
import base64
import struct
import numpy as np
import tensorflow as tf
from threading import Lock
#import threading

import dnnlib.tflib


load_dotenv(dotenv_path = './.env.local')
load_dotenv()


g_Model = None
g_Session = None
g_LoadingMutex = Lock()


def loadModel():
	with g_LoadingMutex:
		global g_Model
		if g_Model:
			return g_Model

		global model_name

		model_path = os.environ.get('MODEL_PATH_%s' % model_name)

		if model_path is None:
			print('invalid model name:', model_path)
			return

		global g_Session
		if g_Session is None:
			print('Initializing dnnlib...')
			dnnlib.tflib.init_tf()
			g_Session = tf.get_default_session()

		print('Loading model %s ...' % model_name)

		with open(model_path, 'rb') as f:
			with g_Session.as_default():
				Gi, Di, Gs = pickle.load(f)
				g_Model = Gs

				## burn one
				#images = Gs.run(np.zeros((1, Gs.input_shape[1])), None, truncation_psi = 0.7, output_transform = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True))
				#print('images:', g_Session, images)

	return g_Model


app = flask.Flask(__name__, static_url_path = '', static_folder = './dist')


@app.route('/')
def root():
	return app.send_static_file('index.html')


@app.route('/spec', methods=['GET'])
def spec():
	#print('spec.pid:', threading.get_ident())
	global model_name
	model = loadModel()

	return dict(model = model_name, latents_dimensions = model.input_shape[1])


@app.route('/generate', methods=['GET'])
def generate():
	#print('generate.pid:', threading.get_ident())
	latentsStr = flask.request.args.get('latents')
	psi = float(flask.request.args.get('psi', 0.5))
	#use_noise = bool(flask.request.args.get('use_noise', True))
	randomize_noise = bool(flask.request.args.get('randomize_noise', True))

	global g_Session
	print('g_Session.1:', g_Session)

	model = loadModel()

	latent_len = model.input_shape[1]
	latents = np.array(struct.unpack('f' * latent_len, base64.b64decode(latentsStr))).reshape([1, latent_len])

	t0 = time.time()

	# Generate image.
	fmt = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True)
	#print('parameters:', latents, psi, use_noise, randomize_noise, fmt)
	with g_Session.as_default():
		images = model.run(latents, None, truncation_psi = psi, randomize_noise = randomize_noise, output_transform = fmt)

	print('generation cost:', time.time() - t0)

	# encode to PNG
	fp = io.BytesIO()
	PIL.Image.fromarray(images[0], 'RGB').save(fp, PIL.Image.registered_extensions()['.png'])

	return flask.Response(fp.getvalue(), mimetype = 'image/png')


def main(argv):
	global model_name
	model_name = argv[1] if len(argv) > 1 else os.environ.get('MODEL_NAME')

	try:
		app.run(port = int(os.getenv('HTTP_PORT')), host = os.getenv('HTTP_HOST'), threaded = False)
	except:
		print('server interrupted:', sys.exc_info())



if __name__ == "__main__":
	main(sys.argv)
