
import os
from dotenv import load_dotenv
import flask


load_dotenv(dotenv_path = './.env.local')
load_dotenv()


app = flask.Flask(__name__, static_url_path = '', static_folder = './dist')


@app.route('/')
def root():
	return app.send_static_file('index.html')


app.run(port = int(os.getenv('HTTP_PORT')), host = os.getenv('HTTP_HOST'))
