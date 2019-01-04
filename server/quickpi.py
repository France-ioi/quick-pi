from flask import Flask
from flask import request
from flask import Response
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

def verifyLock(ipaddr):
	canuse = False
	try:
		file = open("/tmp/lock", "r")
		lockedip = file.read()
		if lockedip == ipaddr:
			canuse = True
		file.close()
	except:
		pass

	return canuse

def veryfyOrTakeLock(ipaddr):
	takelock = False
	canuse = False
	try:
		# Is this quick pi already locked?
		file = open("/tmp/lock", "r")

		lockedip = file.read()

		print(lockedip + " has the lock")
		if lockedip == ipaddr:
			print("This user has the lock")
			# We have the lock we can use this
			canuse = True
	except:
		takelock = True

	if takelock:
		# The quick pi is not locked, take the lock
		print("Nobody has the lock tacking it")
		file = open("/tmp/lock", "w")
		file.write(ipaddr)
		file.close()

		# This user has the lock he can use it
		canuse = True

	return canuse

@app.route("/api/v1/executeprogram", methods=['POST'])
def executeProgram():
	if veryfyOrTakeLock(request.remote_addr):
		print("Executing program by " + request.remote_addr)
		os.system("pkill -f userprogram; python3 cleanup.py")

		file = open("/tmp/userprogram.py", "w")
		file.write(request.data.decode("utf-8"))
		file.close()

		os.system("echo nice -n 19 python3 -u /tmp/userprogram.py &> /tmp/output.txt")
		os.system("bash -c 'nice -n 19 python3 -u /tmp/userprogram.py &> /tmp/output.txt' &")
	else:
		print("Raspberry locked by someone else")
		return Response("Quick Pi locked", 423)

	return "OK"

@app.route("/api/v1/stopprogram", methods=['POST'])
def stopProgram():
	if verifyLock(request.remote_addr):
		print("Stopping program")

		os.system("pkill -f userprogram")
		os.system("python3 cleanup.py")
		os.system("rm /tmp/output.txt")
	else:
		print("Raspberry locked by someone else")
		return Response("Quick Pi locked", 423)

	return "OK"

@app.route("/api/v1/readoutput")
def readOutput():
	output = ""
	if verifyLock(request.remote_addr):
		output = ""
		try:
			file = open("/tmp/output.txt", "r")
			output = file.read()
		except:
			pass
	return output

@app.route("/api/v1/releaselock", methods=['POST'])
def releaseLock():
	if verifyLock(request.remote_addr):
		os.system("rm /tmp/lock")
	else:
		return Response("Quick Pi locked", 423)

	return "OK"


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')

