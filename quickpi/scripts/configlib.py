import collections
import os
import hashlib


def load_settings():
	settings = collections.OrderedDict()
	commentcount = 0
	with open("/boot/quickpi.txt") as quickpiconfigfile:
		for line in quickpiconfigfile:
			if line[0] == '#':
				settings["comment" + str(commentcount)] = line.strip()
				commentcount = commentcount + 1
				continue

			name, value = line.partition("=")[::2]
			name = name.strip()
			value = value.strip()
			if not name:
				continue
			settings[name] = value

	return settings

def save_settings(settings):
	os.system("rm -f /tmp/temp-quickpi.txt")

	f = open("/tmp/temp-quickpi.txt", "w")
	for key in settings:
		if key.startswith("comment"):
			f.write(str(settings[key]) + "\r\n")
		else:
			f.write(key + "=" + str(settings[key]) + "\r\n")

	f.close()

	os.system("sudo mount /boot -o rw,remount")
	os.system("sudo mv -f /tmp/temp-quickpi.txt /boot/quickpi.txt")
	os.system("sudo mount /boot -o ro,remount")

def hash_password(password):
	m = hashlib.sha256()
	m.update("c'est du sel".encode("utf-8"))
	m.update(password.encode("utf-8"))
	hash = m.hexdigest()

	return hash

def validate_password(password):
	settings = load_settings()

	havepassword = False
	rightpass = ""
	try: 
		if settings["WEBCONFIGPASSWORD"]:
			havepassword = True
			rightpass = settings["WEBCONFIGPASSWORD"]

	except:
		pass

	if havepassword:
		if rightpass[0:3] == "XXX" and len(rightpass) == 67:
			hash = hash_password(password)

			return hash == rightpass[3:]

		else:
			return rightpass == password

	return False
