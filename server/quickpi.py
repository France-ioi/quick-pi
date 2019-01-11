from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS
from flask_sockets import Sockets
import os
import gevent
import json

import pexpect

app = Flask(__name__)
CORS(app)

sockets = Sockets(app)

@sockets.route('/api/v1/commands')
def command_socket(ws):
	c = None
	command_mode = False
	run_mode = False

	if os.path.isfile("/tmp/lock.txt"):
		ws.send("Quick Pi locked")

	open("/tmp/lock.txt", "w").close()

	while not ws.closed:
		message = None
		messageJson = None
		with gevent.Timeout(0.5, False):
			message = ws.receive()

		if message is not None:
			messageJson = json.loads(message)

		if run_mode:
			output = ""
			try:
				while True:
					c.expect("\n", 0.01)
					output += c.before
			except pexpect.exceptions.TIMEOUT:
				pass
			except pexpect.exceptions.EOF:
				c = None
				run_mode = False
				command_mode = False
			if output != "":
				ws.send(output)

		if messageJson is None:
			pass
		elif messageJson["command"] == 'startCommandMode':
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			print (" NEW session ");

			file = open("/tmp/quickpi.lib", "w")
			file.write(messageJson["library"])
			file.close()

			c = pexpect.spawnu('/usr/bin/python3 -i /tmp/quickpi.lib')
			c.expect('>>>')

			command_mode = True
			run_mode = False

			print ("-------------")

		elif messageJson["command"] == 'execLine':
			print("Got message " + message[1:])

			if c is None or not command_mode:
				continue

			c.sendline(messageJson["line"])
			c.expect('>>>')

			output = c.before.split("\n", 1)
			result = output[1].strip()

			if result == "":
				result = "none"

			print("Result is " + result)

			ws.send(output[1].strip())
		elif messageJson["command"] == 'startRunMode':
			print ("Starting run mode")
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			file = open("/tmp/userprogram.py", "w")
			file.write(messageJson["program"])
			file.close()

			c = pexpect.spawnu('/usr/bin/python3 /tmp/userprogram.py')

			command_mode = False
			run_mode = True
		elif messageJson["command"] == 'stopAll':
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			command_mode = False
			run_mode = False
		elif messageJson["command"] == "close":
			break


	print ("Clean up ...")
	os.remove("/tmp/lock.txt")
	if c is not None:
		c.terminate()
		os.system("python3 cleanup.py")




if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()

