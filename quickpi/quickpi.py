#new
from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS
from flask_sockets import Sockets
from flask import render_template
from flask import send_from_directory
from flask import redirect
from flask import jsonify
import os
import gevent
import json
import time
import pexpect
import picleanup
import boards
import subprocess
import os
import select
import uuid

app = Flask(__name__)
CORS(app)

sockets = Sockets(app)

distributedGraph = None

distributedMessages = {}
distributedEvents = []


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
	global distributedGraph
	global distributedEvents

	c = None
	longCommand = None
	runningDist = False
	distProcesses = []
	command_mode = False
	command_mode_dirty = False
	command_mode_library = ""
	clean_install = True
	messageArray = None

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
		    "board": currentboard,
		    "version": 1 }

	ws.send(json.dumps(message))


	write_timestamp("connection")

	print ("While not ws.closed")
	while not ws.closed:
		message = None
		messageJson = None

		#print("Waiting for first message")
		if messageArray is not None and len(messageArray) > 0:
			messageJson = messageArray.pop(0)
		else:
			with gevent.Timeout(0.1, False):
				message = ws.receive()

			if message is not None:
				messageJson = json.loads(message)
	#			print("Got message " + messageJson["command"])

		if messageJson is None:
			while len(distributedEvents) > 0:
				message = { "command" : "distributedEvent",
					    "event" : distributedEvents.pop(0) }

				ws.send(json.dumps(message))

			for process in distProcesses:
				exitCode = process["process"].poll()
				if exitCode is not None:
					distProcesses.remove(process)

					if exitCode == 0:
						message = { "command" : "distributedEvent",
							    "event" : { "event" : "nodeStatus", "nodeId": process["nodeId"], "status" : "stopped", "exitCode" : exitCode } }
					else:
						message = { "command" : "distributedEvent",
							    "event" : { "event" : "nodeStatus", "nodeId": process["nodeId"], "status" : "crashed", "exitCode" : exitCode } }

					ws.send(json.dumps(message))



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
		elif messageJson["command"] == 'transaction':
			messageArray = messageJson["messages"]

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
				c.delaybeforesend = None
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
			try:
				os.remove("/tmp/lock")
			except:
				pass

			message = { "command": "closed" }
			ws.send(json.dumps(message))

			print("I got told to close the connection")
			break
		elif messageJson["command"] == "install":
			if clean_install:
				os.system("./install.sh clean")

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
		elif messageJson["command"] == "rundistributed":
			if clean_install:
				os.system("./install.sh clean")

			longCommand = None
			runningDist = True

			write_timestamp("install")

			print("Installing...")
			if c is not None:
				c.terminate()
				os.system("python3 cleanup.py")


			file = open("/tmp/installedprogram.py", "w")
			file.write(messageJson["program"])
			file.close()

			distributedGraph = messageJson["graph"]
			distProcesses = []
			for node in distributedGraph:

				message = { "command" : "distributedEvent",
					    "event" : { "event" : "nodeStatus", "nodeId": node["nodeId"], "status" : "starting" } }
				ws.send(json.dumps(message))

#				os.system("/usr/bin/python3 /tmp/installedprogram.py --nodeid {} &".format(node["nodeId"]))

				print("Starting...")

				process = subprocess.Popen(["/usr/bin/python3", "/tmp/installedprogram.py", "--nodeid", str(node["nodeId"])], stdout=subprocess.PIPE)
				distProcesses.append( {"process" : process, "nodeId" : node["nodeId"] })

				print("Stop..")



				message = { "command" : "distributedEvent",
					     "event" : { "event" : "nodeStatus", "nodeId": node["nodeId"], "status" : "running" } }
				ws.send(json.dumps(message))




			message = { "command": "installed" }
			ws.send(json.dumps(message))

			command_mode = False
			clean_install = True


	print ("Clean up ... ws.closed = ", ws.closed)
	if c is not None:
		c.terminate()
		os.system("python3 cleanup.py")


@app.route('/api/v1/update_image', methods=['POST'])
def upload_update_image():
	print("upload_update_image")
	if request.method == 'POST':
		print("Its a post!")
		if 'firmware_image' not in request.files:
			print("No firmware_image")
			return "fail"
		file = request.files['firmware_image']
		print(file)
		if file.filename == '':
			print("Empty firmware_image")
			return "fail"
		if file:
			print("Saving file");
			try:
				os.unlink("/tmp/quickpi.tar.gz")
			except:
				pass
			file.save("/tmp/quickpi.tar.gz")
			return "ok"

	return "fail"
@sockets.route('/api/v1/update')
def update_socket(ws):
	message = ws.receive()

	version = message.strip()

	print("Trying to upad to version ", version)

	process = subprocess.Popen(["/home/pi/quickpi/scripts/update.sh", version], stdout=subprocess.PIPE)
	poll_obj = select.poll()
	poll_obj.register(process.stdout, select.POLLIN)

	while True:
		poll_result = poll_obj.poll(10000)
		if poll_result:
			output = process.stdout.readline()
			if output == '' and process.poll() is not None:
				break
			if output:
				ws.send(output.decode("utf-8"))
		else:
			break



@app.route('/api/v1/getNodeID')
def getNodeID():
	json = request.get_json()
	print(json)
	return "hello"

#@app.route('/api/v1/getNodeID/<path:nodenumber>')
#def getNodeID(nodenumber):
#	global globalvar
#	globalvar = globalvar + 1
#	return str(globalvar)

@app.route('/api/v1/getNeighbors/<path:nodeid>', methods = ['POST'])
def getNeighbors(nodeid):
	global distributedGraph
	neighbors = []

	for node in distributedGraph:
		if str(node["nodeId"]) == str(nodeid):
			neighbors = node["neighbors"]
			break

	print("Neighbords", nodeid, neighbors)

	return json.dumps(neighbors)

@app.route('/api/v1/getNextMessage/<path:nodeid>', methods = ['POST'])
def getNextMessage(nodeid):
	global distributedEvents
	global distributedMessages

	message = { "hasmessage" : False }
	if (str(nodeid) in distributedMessages) and (len(distributedMessages[str(nodeid)]) > 0):
		messageStruct = distributedMessages[str(nodeid)].pop(0)

		distributedEvents.append( { 'event'   : 'getNextMessage',
					      'messageId': messageStruct["messageId"] } )

		message["value"] = messageStruct["message"]
		message["hasmessage"] = True

	return json.dumps(message)


@app.route('/api/v1/sendMessage/<path:nodeid>', methods = ['POST'])
def sendMessage(nodeid):
	global distributedMessages
	global distributedEvents

	json = request.get_json()
#	print(json)

	messsageId = str(uuid.uuid1())

	distributedEvents.append( { 'event'  : 'sendMessage',
				      'fromId' : json["fromId"],
				      'toId'   : nodeid,
				      'message' : json["message"],
				      'messageId' : messsageId })


	if str(nodeid) not in distributedMessages:
		distributedMessages[str(nodeid)] = []

	distributedMessages[str(nodeid)].append( { 'messageId' : messsageId,
						   'message'   : json["message"] })

#	print(distributedMessages)

	return "OK"


@app.route('/api/v1/submitAnswer/<path:nodeid>', methods = ['POST'])
def submitAnswer(nodeid):
	global distributedEvents
	json = request.get_json()

	distributedEvents.append( { 'event'  : 'submitAnswer',
				      'nodeId' : nodeid,
				      'answer' : json["answer"] } )

	#print(distributedEvents, len(distributedEvents))

	return "OK"


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

	process = subprocess.Popen(["/home/pi/quickpi/scripts/getmac.sh", "wlan0"], stdout=subprocess.PIPE)
	(output, err) = process.communicate()


	settings["WIFIMAC"] = output.decode("utf-8");

	process = subprocess.Popen(["/home/pi/quickpi/scripts/getmac.sh", "eth0"], stdout=subprocess.PIPE)
	(output, err) = process.communicate()
	settings["ETHMAC"] = output.decode("utf-8");


	return json.dumps(settings)


@app.route('/reboot', methods = ['POST'])
def reboot():
        os.system("sudo reboot");

def removewhitespace(inputstring):
	return ''.join(inputstring.split())

@app.route('/savesettings', methods = ['POST'])
def savesettings():
	settings = load_settings()
	json = request.get_json()

	print(json)

	staticnetwork = "0"
	bluetoothenabled = "0"
	useproxy = "0"
	useproxyuser = "0"
	disabletunnel = "0"

	if json["isstaticip"]:
		staticnetwork = "1"

	if json["isbluetoothenabled"]:
		bluetoothenabled = "1"

	if json["useproxy"]:
		useproxy = "1"

	if json["useproxyuser"]:
		useproxyuser = "1"

	if  json["disabletunnel"]:
		disabletunnel = "1"

	os.system("sudo mount /boot -o rw,remount")
	os.system("rm -f /tmp/temp-quickpi.txt")
	f = open("/tmp/temp-quickpi.txt", "w")

	f.write("SSID=" + json["ssid"] + "\r\n")

	if not json["password"].strip():
		print(".....")
		f.write("PASSWORD=" + settings["PASSWORD"] + "\r\n")
	else:
		print("----")
		f.write("PASSWORD=" + json["password"] + "\r\n")

	f.write("STATICNETWORK=" + staticnetwork + "\r\n")
	f.write("STATICIPADDR=" + removewhitespace(json["ip"]) + "\r\n")
	f.write("STATICMASK=" + removewhitespace(json["sn"]) + "\r\n")
	f.write("STATICGATEWAY=" + removewhitespace(json["gw"]) + "\r\n")
	f.write("STATICDNS=" + removewhitespace(json["ns"]) + "\r\n")
	f.write("ENABLEBLUETOOTH=" + bluetoothenabled + "\r\n")
	f.write("NAME=" + removewhitespace(json["qname"]) + "\r\n")
	f.write("SCHOOL=" + removewhitespace(json["school"]) + "\r\n")

	f.write("USEPROXY=" + useproxy + "\r\n")
	f.write("USEPROXYUSER=" + useproxyuser + "\r\n")
	f.write("PROXYADDRESS=" + removewhitespace(json["proxyaddress"]) + "\r\n")
	f.write("PROXYPORT=" + removewhitespace(json["proxyport"]) + "\r\n")
	f.write("PROXYUSER=" + removewhitespace(json["proxyuser"]) + "\r\n")
	f.write("HIDEAPPASSWORD=1\r\n")
	f.write("DISABLETUNNEL=" + disabletunnel + "\r\n")

	if not json["proxypassword"].strip():
		f.write("PROXYPASSWORD=" + settings["PROXYPASSWORD"] + "\r\n")
	else:
		f.write("PROXYPASSWORD=" + removewhitespace(json["proxypassword"]) + "\r\n")

	f.close()

	os.system("sudo cp -f /tmp/temp-quickpi.txt /boot/quickpi.txt")
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
	return redirect("http://192.168.233.3/")


if __name__ == '__main__':
#    app.run(debug=True, host='0.0.0.0')
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    server.serve_forever()
