
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import config



class Handler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.end_headers()
		self.wfile.write(b"Hello.")


try:
	server = HTTPServer(('0.0.0.0', config.server_port), Handler)

	print('gan server start on:', config.server_port)

	server.serve_forever()
except:
	print('server interrupted:', sys.exc_info())
