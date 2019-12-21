
import os
import sys
from dotenv import load_dotenv
import flask
import pickle

import dnnlib.tflib


load_dotenv(dotenv_path = './.env.local')
load_dotenv()


app = flask.Flask(__name__, static_url_path = '', static_folder = './dist')


@app.route('/')
def root():
	return app.send_static_file('index.html')


@app.route('/spec')
def spec():
	global model_name
	global Gs

	return dict(model = model_name, latents_dimensions = Gs.input_shape[1])


def main(argv):
	global model_name

	model_name = argv[1] if len(argv) > 1 else os.environ.get('MODEL_NAME')
	model_path = os.environ.get('MODEL_PATH_%s' % model_name)

	if model_path is None:
		print('invalid model name:', model_path)
		return

	print('Initializing TensorFlow...')

	dnnlib.tflib.init_tf()

	print('Loading model %s ...' % model_name)

	with open(model_path, 'rb') as f:
		global Gs, Gi, Di
		Gi, Di, Gs = pickle.load(f)

	try:
		app.run(port = int(os.getenv('HTTP_PORT')), host = os.getenv('HTTP_HOST'))
	except:
		print('server interrupted:', sys.exc_info())



if __name__ == "__main__":
	main(sys.argv)
