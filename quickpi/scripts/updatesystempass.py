#!/usr/bin/python3
import subprocess
import configlib
import hashlib

def setPassword(userName:str, password:str):
	p = subprocess.Popen([ "/usr/sbin/chpasswd" ], universal_newlines=True, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	(stdout, stderr) = p.communicate(userName + ":" + password + "\n")
	assert p.wait() == 0
	if stdout or stderr:
		raise Exception("Error encountered changing the password!")


#setPassword("pi", "patito")


settings = configlib.load_settings()

updatepassword = False
havepassword = False

try:
	if settings["UPDATESSHPASSWORD"] == "1":
		print("Update ssh password set")
		updatepassword = True
except:
	pass


password = ""
try:
	if settings["WEBCONFIGPASSWORD"]:
		password = settings["WEBCONFIGPASSWORD"]
		havepassword = True
		print("I Have a password")
except:
	pass

if havepassword and password:
	if password[0:3] == "XXX" and len(password) == 67:
		print("It's already a hash")
	else:
		print("Change to a hash")

		hash = configlib.hash_password(password)

		settings["WEBCONFIGPASSWORD"] = "XXX" + hash
		configlib.save_settings(settings)

		if updatepassword:
			setPassword("pi", password)
