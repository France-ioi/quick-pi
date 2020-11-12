#!/usr/bin/python3

import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import subprocess
import os
import argparse
import pigpio
import configlib

parser = argparse.ArgumentParser()
parser.add_argument('--asktocancel', action='store')
args = parser.parse_args()

asktocancel = 0
if args.asktocancel is not None:
	asktocancel = int(args.asktocancel)

UPDATEBASEURL="https://quick-pi.org/update/"
QUICKPIBASEDIR="/home/pi/"

screenwidth = 128
screenheight = 32

RESET=21
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET, GPIO.OUT)
GPIO.output(RESET, 0)
time.sleep(0.01)
GPIO.output(RESET, 1)

UP_PIN=10
DOWN_PIN=9
LEFT_PIN=11
RIGHT_PIN=8
CENTER_PIN=7
BUTTON2_PIN=26
BUZZER_PIN=12
REDLED_PIN=4

RUNAUTOTEST = 1
LEDSHOW = 2
TUNELGAME = 3
PONGGAME = 4

STARTAPMODE = 5
SHOWSCHOOL = 6
SHOWIPADDRESS = 7

RUNAUTOUPDATE = 8

RUNBOARDTEST = 9

ABOUTQUICKPI = 10

SHOWMACADDRESS = 11

STARTBTMODE = 12

main_menu = [ 
##	      { "menu" :  "Auto Test", "submenu" : 
#			[ {"menu" : "Run", "id" :  RUNAUTOTEST } ]},
#              { "menu" : "Sample Programs", "submenu": 
#			[ {"menu" : "Led Show", "id" : LEDSHOW},
#			  {"menu" : "Tunel game", "id": TUNELGAME},
#			  {"menu" : "Pong game", "id" : PONGGAME} ]},
	      { "menu" : "Configuration", "submenu": 
			[ {"menu" : "Start Access Point mode", "id" : STARTAPMODE },
			  {"menu" : "Start BT network", "id" : STARTBTMODE },
			  {"menu" : "Show school and name", "id" : SHOWSCHOOL },
			  {"menu" : "Show IP Address", "id" : SHOWIPADDRESS }, 
			  {"menu" : "Show Mac Address", "id" : SHOWMACADDRESS } ]},
 
              { "menu" :  "Check for updates", "id" :  RUNAUTOUPDATE },
              { "menu" :  "Board test", "submenu": 
			[ { "menu" : "Press to run", "id" :  RUNBOARDTEST } ] },
              { "menu" : "About QuickPi", "id": ABOUTQUICKPI }

]


GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CENTER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(REDLED_PIN, GPIO.OUT)
GPIO.output(REDLED_PIN, GPIO.LOW)


pi = pigpio.pi()
def changePassiveBuzzerState(pin, state):
	state = int(state)

	pi.set_mode(pin, pigpio.OUTPUT)

	pi.wave_clear()
	pi.wave_tx_stop()

	if state:
		wf = []

		wf.append(pigpio.pulse(1<<pin, 0, 500))
		wf.append(pigpio.pulse(0, 1<<pin, 500))

		pi.wave_add_generic(wf)
		a = pi.wave_create()
		pi.wave_send_repeat(a)
	else:
		pi.wave_tx_stop()
		GPIO.setup(pin, GPIO.OUT)
		GPIO.output(pin, GPIO.LOW)


serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32)
device.cleanup = lambda _: True

frames = 0
start = time.time()
#canvas = canvas(device)
oledimage = Image.new('1', (128, 32))
draw = ImageDraw.Draw(oledimage)
oledfont = ImageFont.load_default()

settings = configlib.load_settings()


logo = Image.open("/home/pi/quickpi/scripts/franceio.png").convert("1")
oledimage.paste(logo, box=(int(0), 0))

draw.text((60, 0), settings["SCHOOL"], font=oledfont, fill=255)
draw.text((60, 18), settings["NAME"], font=oledfont, fill=255)
device.display(oledimage)

time.sleep(5)


def displayText(line1, line2, line3):
	draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)
	draw.text((0, 0), line1, font=oledfont, fill=255)
	draw.text((0, 11), line2, font=oledfont, fill=255)
	draw.text((0, 21), line3, font=oledfont, fill=255)

	device.display(oledimage)

def drawMenu(topLabel, mainLabel, arrows):
	draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)

	draw.text((0, 0), topLabel, font=oledfont, fill=255)

	draw.text((10, 18), mainLabel, font=oledfont, fill=255)


	if arrows:
		draw.polygon([(117, 13), (127, 13), (122,2)], fill=255)
		draw.polygon([(117, 19), (127, 19), (122,30)], fill=255)


	device.display(oledimage)

start = 0
end = 310

def drawLoading():
	global start, end
	draw.rectangle((117, 0, 127, 31), outline=0, fill=0)

	draw.pieslice([(117, 0), (127,31)], start = start, end = end, fill=255)

	start = start + 10
	end = end + 10

	if start == 370:
		start = 0
	if end == 370:
		end = 0

	device.display(oledimage)


def waitForButton(buttons, wait=True):
	keepgoing = True
	while keepgoing:
		for button in buttons:
			if GPIO.input(button):
				changePassiveBuzzerState(BUZZER_PIN, 1)
				GPIO.output(REDLED_PIN, GPIO.HIGH)
				time.sleep(0.050)
				changePassiveBuzzerState(BUZZER_PIN, 0)
				GPIO.output(REDLED_PIN, GPIO.LOW)
				return button
		keepgoing = wait
		time.sleep(0.05)
		if os.path.isfile("/tmp/time-connection"):
			draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)
			device.display(oledimage)
			exit(0)


def getCommandOutput(cmd):
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	(output, err) = process.communicate()

	return output

def curlErrorToString(result):
	if result == 3:
		return "Url malformat"
	elif result == 5:
		return "Couldn't resolve proxy"
	elif result == 6:
		return "Couldn't resolve host"
	elif result == 7:
		return "Couldn't connect to host"
	elif result == 9:
		return "Access defined"
	elif result == 22:
		return "HTTP returned error"
	elif result == 35:
		return "TLS error"
	elif result == 48:
		return "Can't verify host"
	elif result == 60:
		return "Peer certificate cannot be authenticated"

	return str(result)


if asktocancel > 0:

	start = time.time()
	oldtimeleft = asktocancel
	while True:
		retval = waitForButton([UP_PIN, DOWN_PIN, LEFT_PIN, RIGHT_PIN, CENTER_PIN, BUTTON2_PIN], False)

		if retval is not None:
			displayText("", "", "")
			exit(42)

		timeleft = int(asktocancel - (time.time() - start))
		if timeleft != oldtimeleft:
			displayText("Running installed program", "press any key to cancel", str(timeleft))
			oldtimeleft = timeleft

		if timeleft <= 0:
			displayText("", "", "")
			exit (0)


if settings["SCHOOL"] == "schoolkey" and settings["NAME"] == "quickpi1":
	drawMenu("Use Access Point or USB", "to configure this board", False)
	
	draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)
	draw.text((0, 0),  "Use access Point or", font=oledfont, fill=255)
	draw.text((0, 10), "USB to configure this", font=oledfont, fill=255)
	draw.text((0, 20), "board. Press button.", font=oledfont, fill=255)

	device.display(oledimage)

	waitForButton([UP_PIN, DOWN_PIN, LEFT_PIN, BUTTON2_PIN])

currentMenuPos = 0
currentMenu = main_menu
menuStack = []
titleStack = []
currentTitle = "Main menu"
titleStack.append(currentTitle)
while True:
	if os.path.isfile("/tmp/time-connection"):
		break

	if currentTitle is not None:
		drawMenu(currentTitle, currentMenu[currentMenuPos]["menu"], True)
		print(currentMenu[currentMenuPos])

	time.sleep(0.2)
	pressed = waitForButton([UP_PIN, DOWN_PIN, LEFT_PIN, BUTTON2_PIN])
	if pressed == DOWN_PIN:
		if currentMenu is not None:
			currentMenuPos = currentMenuPos + 1
			if currentMenuPos == len(currentMenu):
				currentMenuPos = 0
	elif pressed == UP_PIN:
		if currentMenu is not None:
			if currentMenuPos == 0:
				currentMenuPos = len(currentMenu) - 1
			else:
				currentMenuPos = currentMenuPos - 1
	elif pressed == LEFT_PIN:
		if currentMenu is not main_menu:
			currentMenuPos = 0
			currentMenu = menuStack.pop()
			currentTitle = titleStack.pop()

	elif pressed == BUTTON2_PIN:
		if currentMenu is None:
			continue

		if "submenu" in currentMenu[currentMenuPos]:
			print("Changing submenu to ", currentMenu[currentMenuPos]["submenu"])
			menuStack.append(currentMenu)
			titleStack.append(currentTitle)
			currentTitle = currentMenu[currentMenuPos]["menu"]
			currentMenu = currentMenu[currentMenuPos]["submenu"]
			#print ("New title ...", currentMenu[currentMenuPos])
			currentMenuPos = 0
		else:
			menuoption = currentMenu[currentMenuPos]["id"]

#			menuStack.append(currentMenu)
#			titleStack.append(currentTitle)
#			currentTitle = None
#			currentMenu = None

			if menuoption == STARTAPMODE:
				settings = configlib.load_settings()
				showPassword = True
				try:
					if settings["HIDEAPPASSWORD"] == "1":
						showPassword = False
				except:
					pass


				wifiname = "QP-" + settings["NAME"]

				if showPassword:
					drawMenu("Connect to: " + wifiname, "pass: France-ioi", False)
				else:
					drawMenu("Connect to:", wifiname, False)


				os.system("/home/pi/quickpi/scripts/startap.sh ap &")

				while True:
					drawLoading()
					time.sleep(0.05)
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
#						currentMenu = menuStack.pop()
#						currentTitle = titleStack.pop()
						os.system("/home/pi/quickpi/scripts/startap.sh station &")
						break


			elif menuoption == SHOWSCHOOL:
				settings = configlib.load_settings()
				drawMenu(settings["SCHOOL"], settings["NAME"], False)
				pressed = waitForButton([LEFT_PIN], False)
				while True:
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
						break


			elif menuoption == SHOWIPADDRESS:
				ethipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getip.sh", "eth0"]).decode("ascii").strip()
				usbipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getip.sh", "usb0"]).decode("ascii").strip()
				wlanipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getip.sh", "wlan0"]).decode("ascii").strip()
				btipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getip.sh", "pan0"]).decode("ascii").strip()

				ipaddresses = []
				if wlanipaddress:
					ipaddresses.append(["WIFI", wlanipaddress])

				if ethipaddress:
					ipaddresses.append(["Cable", ethipaddress])

				if usbipaddress:
					ipaddresses.append(["USB", usbipaddress])

				if btipaddress:
					ipaddresses.append(["BT", btipaddress])

				ipindex = 0
				morethanone = len(ipaddresses) > 1

				if len(ipaddresses) == 0:
					drawMenu("IP Address", "No IP", False)
				else:
					drawMenu("IP Address - " + ipaddresses[ipindex][0], ipaddresses[ipindex][1], morethanone)

				while True:
					pressed = waitForButton([LEFT_PIN, UP_PIN, DOWN_PIN], True)
					if pressed == LEFT_PIN:
						break
					elif pressed == UP_PIN:
						ipindex = ipindex - 1;
						if ipindex == -1:
							ipindex = len(ipaddresses) - 1
					elif pressed == DOWN_PIN:
						ipindex = ipindex + 1
						if ipindex == len(ipaddresses):
							ipindex = 0

					if len(ipaddresses) > 0:
						drawMenu("IP Address - " + ipaddresses[ipindex][0], ipaddresses[ipindex][1], morethanone)
					time.sleep(0.2)

			elif menuoption == SHOWMACADDRESS:
				ethipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getmac.sh", "eth0"]).decode("ascii").strip()
				wlanipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getmac.sh", "wlan0"]).decode("ascii").strip()

				ipaddresses = []
				if wlanipaddress:
					ipaddresses.append(["WIFI", wlanipaddress])

				if ethipaddress:
					ipaddresses.append(["Cable", ethipaddress])

				ipindex = 0
				morethanone = len(ipaddresses) > 1

				if len(ipaddresses) == 0:
					drawMenu("Mac Address", "No network int", False)
				else:
					drawMenu("Mac Address " + ipaddresses[ipindex][0], ipaddresses[ipindex][1], morethanone)

				while True:
					pressed = waitForButton([LEFT_PIN, UP_PIN, DOWN_PIN], True)
					if pressed == LEFT_PIN:
						break
					elif pressed == UP_PIN:
						ipindex = ipindex - 1;
						if ipindex == -1:
							ipindex = len(ipaddresses) - 1
					elif pressed == DOWN_PIN:
						ipindex = ipindex + 1
						if ipindex == len(ipaddresses):
							ipindex = 0

					if len(ipaddresses) > 0:
						drawMenu("Mac Address " + ipaddresses[ipindex][0], ipaddresses[ipindex][1], morethanone)
					time.sleep(0.2)



			elif menuoption == RUNBOARDTEST:
				os.system("python3 /home/pi/quickpi/testsuite/fulltest.py")

				waitForButton([UP_PIN, DOWN_PIN, LEFT_PIN, BUTTON2_PIN])

			elif menuoption == RUNAUTOUPDATE:
				file = open('/home/pi/quickpi/version',mode='r')
				currentversion = file.read()
				file.close()

				ethipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getip.sh", "eth0"]).decode("ascii").strip()
				wlanipaddress = getCommandOutput(["/home/pi/quickpi/scripts/getip.sh", "wlan0"]).decode("ascii").strip()

				keepgoing = True
				if (not ethipaddress) and (not wlanipaddress):
					drawMenu("Connect to wifi: ", "Or use config page", False)

					while True:
						pressed = waitForButton([LEFT_PIN], False)

						if pressed == LEFT_PIN:
							keepgoing = False
							break

				if not keepgoing:
					continue


				drawMenu("Current version: " + str(currentversion), "Press to check", False)
				time.sleep(0.1)

				keepgoing = False
				while True:
					pressed = waitForButton([LEFT_PIN, BUTTON2_PIN], False)
					if pressed == LEFT_PIN:
						keepgoing = False
						break
					elif pressed == BUTTON2_PIN:
						keepgoing = True
						break

				if not keepgoing:
					continue

				time.sleep(1)

				try:
					os.remove("/tmp/version")
				except:
					pass
				result = os.system("curl -f " + UPDATEBASEURL + "version --output /tmp/version") >> 8

				if result != 0:
					errorstr = curlErrorToString(result)
					drawMenu("Auto update failed", errorstr, False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				file = open('/tmp/version',mode='r')
				newversion = file.read()
				file.close()

				newversion = int(newversion.strip())
				currentversion = int(currentversion.strip())

				if newversion <= currentversion:
					drawMenu("Auto update", "Already at " + str(currentversion), False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				drawMenu("Auto update", "Downloading " + str(newversion), False)
				time.sleep(1)

				result = os.system("curl -f " + UPDATEBASEURL + "quickpi.tar.gz --output /tmp/quickpi.tar.gz") >> 8

				if result != 0:
					drawMenu("Auto update failed", "Failed to download " + str(result) , False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				drawMenu("Auto update", "Uncompressing update", False)
				time.sleep(1)
				result = os.system("sudo mount / -o remount,rw")

				if result == 0:
					result = os.system("tar xvfzp /tmp/quickpi.tar.gz -C /home/pi/")

				if result != 0:
					drawMenu("Auto update", "Failed uncompressupdate", False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				drawMenu("Auto update", "Upkeeping ...", False)
				time.sleep(1)
				os.system("cp -f /tmp/version /home/pi/quickpi/")
				result = os.system("/home/pi/quickpi/scripts/afterupdate.sh")


				drawMenu("Auto update", "Success, restarting...", False)
				os.system("sudo reboot")
				while True:
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
						break
					continue
			elif menuoption == ABOUTQUICKPI:
				drawMenu("By France-ioi", "quick-pi.org", False)
				while True:
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
						break
			elif menuoption == STARTBTMODE:
				bluetoothon = False
				try:
					bluetoothon = settings["ENABLEBLUETOOTH"] == "1"
				except:
					pass

				if bluetoothon:
					drawMenu("BT network", "Bluetooth already on", False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				else:
					drawMenu("BT network", "Connect: " + settings["NAME"],  False)

					os.system("/home/pi/quickpi/scripts/startbluetooth.sh start &")

					while True:
						drawLoading()
						time.sleep(0.05)
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							currentMenu = menuStack.pop()
							currentTitle = titleStack.pop()
							os.system("/home/pi/quickpi/scripts/startbluetooth.sh stop &")
							break




draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)
device.display(oledimage)

