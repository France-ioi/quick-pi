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
import picleanup

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
	command_mode_dirty = False
	command_mode_library = ""
	clean_install = True

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

	quickpiname = "quickpi"
	try:
		quickpiname = os.environ['NAME']
	except:
		pass

	message = { "command": "hello",
		    "name": quickpiname }
	ws.send(json.dumps(message))


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
#			print("Got message " + messageJson["command"])

		if messageJson is None:
			pass
		elif messageJson["command"] == 'ping':
			message = { "command": "pong" }
			ws.send(json.dumps(message))

		elif messageJson["command"] == 'startCommandMode':
			if clean_install:
				os.system("./install.sh clean &")
				clean_install = False

			# Only reload the python process if we changed the python library
			# or weren't in command mode previously
			startNewProcess = False
			if (not command_mode) or (command_mode_library != messageJson["library"]):
				print("Changed library");
				if c is not None:
					c.terminate()
				startNewProcess = True


			# Only run cleanup if we were actually did something with the previous session
			if (not command_mode) or command_mode_dirty:
				print("Is dirty")
				picleanup.docleanup()
				#os.system("python3 cleanup.py")

			write_timestamp("session")

			print ("NEW session ");

			if command_mode_library != messageJson["library"]:
				file = open("/tmp/quickpi.lib", "w")
				file.write(messageJson["library"])
				file.close()

			if startNewProcess:
				print ("Starting new process")
				c = pexpect.spawnu('/usr/bin/python3 -i /tmp/quickpi.lib')
				c.expect('>>>')

			command_mode_library = messageJson["library"]
			command_mode_dirty = False
			command_mode = True

			message = { "command": "startCommandMode" }
			ws.send(json.dumps(message))

		elif messageJson["command"] == 'execLine':
#			print("Executing command: [" + messageJson["line"] + "]")

			seq = 0
			try:
				seq = messageJson["seq"]
			except:
				pass

			if c is None or not command_mode:
				print("Not in command mode")

				message = { "command": "execLineresult",
						"result": "0",
						"error": "not in command mode",
						"seq": seq
					  }

				ws.send(json.dumps(message))

				continue

			command_mode_dirty = True

			c.sendline(messageJson["line"])
			c.expect('>>>')

			output = c.before.split("\n", 1)
			result = output[1].strip()

			if result == "":
				result = "none"

			print("Result is " + result)

			message = { "command": "execLineresult",
				    "result": output[1].strip(),
				    "seq": seq
				  }

			ws.send(json.dumps(message))

		elif messageJson["command"] == 'stopAll':
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			command_mode = False
		elif messageJson["command"] == "close":
			os.remove("/tmp/lock")
			break
		elif messageJson["command"] == "install":
			if clean_install:
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
			clean_install = True

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
