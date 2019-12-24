
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
import json

import dnnlib.tflib
from training import misc
from projector import Projector



load_dotenv(dotenv_path = './.env.local')
load_dotenv()


g_Gs = None
g_Lpips = None
g_Projector = None
g_Session = None
g_LoadingMutex = Lock()


def loadGs():
	with g_LoadingMutex:
		global g_Gs
		if g_Gs:
			return g_Gs

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
				g_Gs = Gs

				## burn one
				#images = Gs.run(np.zeros((1, Gs.input_shape[1])), None, truncation_psi = 0.7, output_transform = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True))
				#print('images:', g_Session, images)

	return g_Gs


def loadLpips():
	with g_LoadingMutex:
		global g_Lpips
		if g_Lpips:
			return g_Lpips

		model_path = os.environ.get('MODEL_PATH_LPIPS')

		if model_path is None:
			print('invalid model name:', model_path)
			return

		global g_Session
		if g_Session is None:
			print('Initializing dnnlib...')
			dnnlib.tflib.init_tf()
			g_Session = tf.get_default_session()

		print('Loading model lpips ...')

		with open(model_path, 'rb') as f:
			with g_Session.as_default():
				lpips = pickle.load(f)
				g_Lpips = lpips

	return g_Lpips


def loadProjector():
	global g_Projector
	if g_Projector:
		return g_Projector

	gs = loadGs()
	lpips = loadLpips()

	g_Projector = Projector()
	g_Projector.set_network(gs, lpips)

	return g_Projector


app = flask.Flask(__name__, static_url_path = '', static_folder = './dist')


@app.route('/')
def root():
	return app.send_static_file('index.html')


@app.route('/projector/')
def projector():
	return app.send_static_file('projector.html')


@app.route('/spec', methods=['GET'])
def spec():
	global model_name
	model = loadGs()

	return dict(model = model_name, latents_dimensions = model.input_shape[1])


@app.route('/generate', methods=['GET'])
def generate():
	latentsStr = flask.request.args.get('latents')
	psi = float(flask.request.args.get('psi', 0.5))
	#use_noise = bool(flask.request.args.get('use_noise', True))
	randomize_noise = int(flask.request.args.get('randomize_noise', 1))

	global g_Session
	print('g_Session.1:', g_Session)

	model = loadGs()

	latent_len = model.input_shape[1]
	latents = np.array(struct.unpack('f' * latent_len, base64.b64decode(latentsStr))).reshape([1, latent_len])

	t0 = time.time()

	# Generate image.
	fmt = dict(func = dnnlib.tflib.convert_images_to_uint8, nchw_to_nhwc = True)
	with g_Session.as_default():
		images = model.run(latents, None, truncation_psi = psi, randomize_noise = randomize_noise != 0, output_transform = fmt)

	print('generation cost:', time.time() - t0)

	# encode to PNG
	fp = io.BytesIO()
	PIL.Image.fromarray(images[0], 'RGB').save(fp, PIL.Image.registered_extensions()['.png'])

	return flask.Response(fp.getvalue(), mimetype = 'image/png')


@app.route('/project', methods=['POST'])
def project():
	steps = int(flask.request.args.get('steps', 1000))
	yieldInterval = int(flask.request.args.get('yieldInterval', 10))

	imageFile = flask.request.files.get('image')
	if not imageFile:
		flask.abort(400, 'image field is requested.')

	image = PIL.Image.open(imageFile.stream)
	#image.save('./test.png')

	image_array = np.array(image)[:, :, :3].swapaxes(0, 2).swapaxes(1, 2)
	image_array = misc.adjust_dynamic_range(image_array, [0, 255], [-1, 1])

	#print('shape:', image_array.shape)

	def gen():
		proj = loadProjector()
		proj.start([image_array])
		for step in proj.runSteps(steps):
			print('\rProjecting: %d / %d' % (step, steps), end = '', flush = True)
			if step % yieldInterval == 0:
				dlatents = proj.get_dlatents()
				images = proj.get_images()
				pilImage = misc.convert_to_pil_image(misc.create_image_grid(images), drange = [-1,1])

				fp = io.BytesIO()
				pilImage.save(fp, PIL.Image.registered_extensions()['.png'])

				imgUrl = 'data:image/png;base64,%s' % base64.b64encode(fp.getvalue()).decode('ascii')

				latentsList = list(dlatents.reshape((-1, dlatents.shape[2])))
				latentCodes = list(map(lambda latents: base64.b64encode(struct.pack('f' * latents.shape[0], *latents)).decode('ascii'), latentsList))

				yield json.dumps(dict(img = imgUrl, latentCodes = latentCodes)) + '\n\n'

	return flask.Response(gen(), mimetype='text/plain')


def main(argv):
	global model_name
	model_name = argv[1] if len(argv) > 1 else os.environ.get('MODEL_NAME')

	try:
		app.run(port = int(os.getenv('HTTP_PORT')), host = os.getenv('HTTP_HOST'), threaded = False)
	except:
		print('server interrupted:', sys.exc_info())



if __name__ == "__main__":
	main(sys.argv)
