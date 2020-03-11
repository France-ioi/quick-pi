#new
from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS
from flask_sockets import Sockets
from flask import render_template
from flask import send_from_directory
from flask import redirect
import os
import gevent
import json
import time
import pexpect
import picleanup
import boards
import subprocess
import os

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
	longCommand = None
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

	currentboard = boards.detectBoard()

	message = { "command": "hello",
		    "name": quickpiname,
		    "board": currentboard }
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
			if longCommand is not None:
				print("Checking on long command")
				messageJson = longCommand
				seq = 0
				try:
					seq = messageJson["seq"]
				except:
					pass

				try:
					c.expect('>>>', timeout=1)
					longCommand = None
				except pexpect.exceptions.TIMEOUT:
					print("TIMEOUT!!!!!!")

				if longCommand is None:
					output = c.before.split("\n", 1)
					result = output[1].strip()

					if result == "":
						result = "none"

					print(messageJson["line"], "Result is", result, "seq", seq)

					message = { "command": "execLineresult",
						    "result": output[1].strip(),
						    "seq": seq
						  }

					ws.send(json.dumps(message))
		elif messageJson["command"] == 'ping':
			message = { "command": "pong" }
			ws.send(json.dumps(message))

		elif messageJson["command"] == 'startCommandMode':
			if clean_install:
				os.system("./install.sh clean &")
				clean_install = False

			startNewProcess = False
			# Only reload the python process if we changed the python library
			# or weren't in command mode previously
			if (not command_mode) or (command_mode_library != messageJson["library"] or longCommand):
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
			longCommand = None

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

			longCommand = None
			seq = 0
			long = False
			try:
				seq = messageJson["seq"]
			except:
				print("Command has no sequence!")
				pass

			try:
				long = messageJson["long"]
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

			try:
				c.expect('>>>', timeout=5)
			except pexpect.exceptions.TIMEOUT:
				print("TIMEOUT!!!!!!")
				longCommand = messageJson

			if longCommand is None:
				output = c.before.split("\n", 1)
				result = output[1].strip()

				if result == "":
					result = "none"

				print(messageJson["line"], "Result is", result, "seq", seq)

				message = { "command": "execLineresult",
					    "result": output[1].strip(),
					    "seq": seq
					  }

				ws.send(json.dumps(message))

		elif messageJson["command"] == 'stopAll':
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")

			longCommand = None
			command_mode = False
		elif messageJson["command"] == "close":
			os.remove("/tmp/lock")
			break
		elif messageJson["command"] == "install":
			if clean_install:
				os.system("./install.sh clean &")

			longCommand = None

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



@app.route('/log/<path:path>')
def syslog(path):
	output = ""
	if path == "syslog":
		process = subprocess.Popen(["logread"], stdout=subprocess.PIPE)
		(output, err) = process.communicate()
	elif path == "dmesg":
		process = subprocess.Popen(["dmesg"], stdout=subprocess.PIPE)
		(output, err) = process.communicate()
	elif path == "journalctl":
		process = subprocess.Popen(["journalctl"], stdout=subprocess.PIPE)
		(output, err) = process.communicate()


	return output

@app.route('/wifinetworks.json')
def wifi_networks():
	process = subprocess.Popen(["bash", "-c", "sudo iwlist scan|grep ESSID| cut -d \":\" -f 2"], stdout=subprocess.PIPE)
	(output, err) = process.communicate()

	x = output.decode("ascii").replace('"', '')
	parts = x.split()

	parts = list(dict.fromkeys(parts))

	return json.dumps(parts)

def load_settings():
	settings = {}
	with open("/boot/quickpi.txt") as quickpiconfigfile:
		for line in quickpiconfigfile:
			if line[0] == '#':
				continue

			name, value = line.partition("=")[::2]
			name = name.strip()
			value = value.strip()
			if not name:
				continue
			settings[name] = value

	return settings

@app.route('/getsettings.json')
def getsettings():
	settings = load_settings()

	return json.dumps(settings)


@app.route('/savesettings', methods = ['POST'])
def savesettings():
	settings = load_settings()
	json = request.get_json()

	print(json)

	staticnetwork = "0"
	bluetoothenabled = "0"
	useproxy = "0"
	useproxyuser = "0"

	if json["isstaticip"]:
		staticnetwork = "1"

	if json["isbluetoothenabled"]:
		bluetoothenabled = "1"

	if json["useproxy"]:
		useproxy = "1"

	if json["useproxyuser"]:
		useproxyuser = "1"

	os.system("sudo mount /boot -o rw,remount")
	f = open("/boot/quickpi.txt", "w")

	f.write("SSID=" + json["ssid"] + "\r\n")

	if not json["password"].strip():
		print(".....")
		f.write("PASSWORD=" + settings["PASSWORD"] + "\r\n")
	else:
		print("----")
		f.write("PASSWORD=" + json["password"] + "\r\n")

	f.write("STATICNETWORK=" + staticnetwork + "\r\n")
	f.write("STATICIPADDR=" + json["ip"] + "\r\n")
	f.write("STATICIPADDR=" + json["sn"] + "\r\n")
	f.write("STATICGATEWAY=" + json["gw"] + "\r\n")
	f.write("STATICDNS=" + json["ns"] + "\r\n")
	f.write("ENABLEBLUETOOTH=" + bluetoothenabled + "\r\n")
	f.write("NAME=" + json["qname"] + "\r\n")
	f.write("SCHOOL=" + json["school"] + "\r\n")

	f.write("USEPROXY" + useproxy + "\r\n")
	f.write("USEPROXYUSER" + useproxyuser + "\r\n")
	f.write("PROXYADDRESS=" + json["proxyaddress"] + "\r\n")
	f.write("PROXYPORT=" + json["proxyport"] + "\r\n")
	f.write("PROXYUSER=" + json["proxyuser"] + "\r\n")

	if not json["proxypassword"].strip():
		f.write("PROXYPASSWORD=" + settings["PROXYPASSWORD"] + "\r\n")
	else:
		f.write("PROXYPASSWORD=" + json["proxypassword"] + "\r\n")

	f.close()

	os.system("sudo mount /boot -o ro,remount")

	print (request.get_json())
	return "OK"


@app.route('/static/<path:path>')
def send_statuc(path):
	return send_from_directory('static', path)


@app.route('/')
def index():
	return send_from_directory('.', "index.html")



@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):	
	print("Trying to access ", path)
	return redirect("http://192.168.233.2/")


if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
