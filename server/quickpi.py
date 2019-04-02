from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS
from flask_sockets import Sockets
import os
import gevent
import json
import time

import pexpect

app = Flask(__name__)
CORS(app)

sockets = Sockets(app)

def veryfyOrTakeLock(username):
	takelock = False
	canuse = False
	try:
		# Is this quick pi already locked?
		file = open("/tmp/lock", "r")

		lockedusername = file.read()

		print(lockedusername + " has the lock")
		if lockedusername == username:
			print("This user has the lock")
			# We have the lock we can use this
			canuse = True
	except:
		takelock = True

	if takelock:
		# The quick pi is not locked, take the lock
		print("Nobody has the lock tacking it")
		file = open("/tmp/lock", "w")
		file.write(username)
		file.close()

		# This user has the lock he can use it
		canuse = True

	return canuse, username

def write_timestamp(type):
	file = open("/tmp/time-" + type, "w")
	file.write(str(int(time.time())))
	file.close()


@sockets.route('/api/v1/commands')
def command_socket(ws):
	c = None
	command_mode = False
	run_mode = False

	print (".")
	message = ws.receive()
	print ("First message was " + message)

	if message is not None:
		print ("Converting to json")
		messageJson = json.loads(message)
		## First message has to be grabLock
		if messageJson["command"] != 'grabLock':
			print ("Was expecting grabLock Message")
			return

		print ("Verifying lock")
		canuse, lockeduser = veryfyOrTakeLock(messageJson["username"])
		if not canuse:
			message = { "command": "locked",
				    "lockedby": lockeduser }

			print("Pi is locked by " + lockeduser)
			ws.send(json.dumps(message))
			return

	write_timestamp("connection")

	print ("While not ws.closed")
	while not ws.closed:
		message = None
		messageJson = None

		#print("Waiting for first message")
		with gevent.Timeout(0.5, False):
			message = ws.receive()

		if message is not None:
			messageJson = json.loads(message)
			print("Got message " + messageJson["command"])

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
		elif messageJson["command"] == 'ping':
			message = { "command": "pong" }
			ws.send(json.dumps(message))

		elif messageJson["command"] == 'startCommandMode':
			os.system("./install.sh clean &")

			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			write_timestamp("session")

			print ("NEW session ");

			file = open("/tmp/quickpi.lib", "w")
			file.write(messageJson["library"])
			file.close()

			c = pexpect.spawnu('/usr/bin/python3 -i /tmp/quickpi.lib')
			c.expect('>>>')

			command_mode = True
			run_mode = False

			message = { "command": "startCommandMode" }
			ws.send(json.dumps(message))

			print ("-------------")

		elif messageJson["command"] == 'execLine':
			print("Executing command: [" + messageJson["line"] + "]")

			if c is None or not command_mode:
				print("Not in command mode")

				message = { "command": "execLineresult",
						"result": "0",
						"error": "not in command mode" }

				ws.send(json.dumps(message))

				continue

			c.sendline(messageJson["line"])
			c.expect('>>>')

			output = c.before.split("\n", 1)
			result = output[1].strip()

			if result == "":
				result = "none"

			print("Result is " + result)


			message = { "command": "execLineresult",
					"result": output[1].strip() }

			ws.send(json.dumps(message))

		elif messageJson["command"] == 'startRunMode':
			print ("Starting run mode")
			os.system("./install.sh clean &")

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
			os.remove("/tmp/lock")
			break
		elif messageJson["command"] == "install":
			os.system("./install.sh clean &")

			write_timestamp("install")

			print("Installing...")
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			file = open("/tmp/installedprogram.py", "w")
			file.write(messageJson["program"])
			file.close()

			os.system("nice -n 19 /usr/bin/python3 /tmp/installedprogram.py &")
			os.system("./install.sh install /tmp/installedprogram.py &")


			message = { "command": "installed" }
			ws.send(json.dumps(message))

			command_mode = False
			run_mode = False

	print ("Clean up ...")
	if c is not None:
		c.terminate()
		os.system("python3 cleanup.py")


if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
