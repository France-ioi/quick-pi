#!/usr/bin/python3

import time
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import RPi.GPIO as GPIO
import subprocess
import os

UPDATEBASEURL="https://mapadev.com/test/quickpi/"
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

RUNAUTOTEST = 1
LEDSHOW = 2
TUNELGAME = 3
PONGGAME = 4

STARTAPMODE = 5
SHOWSCHOOL = 6
SHOWIPADDRESS = 7

RUNAUTOUPDATE = 8

main_menu = [ 
##	      { "menu" :  "Auto Test", "submenu" : 
#			[ {"menu" : "Run", "id" :  RUNAUTOTEST } ]},
#              { "menu" : "Sample Programs", "submenu": 
#			[ {"menu" : "Led Show", "id" : LEDSHOW},
#			  {"menu" : "Tunel game", "id": TUNELGAME},
#			  {"menu" : "Pong game", "id" : PONGGAME} ]},
	      { "menu" : "Configuration", "submenu": 
			[ {"menu" : "Start Access Point mode" , "id" : STARTAPMODE },
			  {"menu" : "Show school and name", "id" : SHOWSCHOOL },
			  {"menu" : "Show IP Address", "id" : SHOWIPADDRESS } ]},
              { "menu" :  "Check for updates", "submenu" :
                        [ {"menu" : "Check Now", "id" :  RUNAUTOUPDATE } ]}

]


GPIO.setup(UP_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(DOWN_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(LEFT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(RIGHT_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CENTER_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32)
device.cleanup = lambda _: True

frames = 0
start = time.time()
#canvas = canvas(device)
oledimage = Image.new('1', (128, 32))
draw = ImageDraw.Draw(oledimage)
oledfont = ImageFont.load_default()


logo = Image.open("/home/pi/quickpi/scripts/franceio.png").convert("1")
oledimage.paste(logo, box=(int(64 - (logo.width / 2)), 0))
device.display(oledimage)

time.sleep(3)

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
				return button
		keepgoing = wait
		time.sleep(0.05)

def getCommandOutput(cmd):
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	(output, err) = process.communicate()

	return output

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
				drawMenu("Connect to network", "QuickPi", False)
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
				settings = load_settings()
				drawMenu(settings["SCHOOL"], settings["NAME"], False)
				pressed = waitForButton([LEFT_PIN], False)
				while True:
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
						break


			elif menuoption == SHOWIPADDRESS:
				ipaddress = getCommandOutput(["hostname", "-I"]).decode("ascii").strip()
				drawMenu("IP Address", ipaddress, False)
				while True:
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
						break


			elif menuoption == RUNAUTOUPDATE:
				drawMenu("Auto update", "Checking ...", False)
				time.sleep(1)

				try:
					os.remove("/tmp/version")
				except:
					pass
				result = os.system("curl -f " + UPDATEBASEURL + "version --output /tmp/version")

				if result != 0:
					drawMenu("Auto update", "Failed error " + str(result), False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				file = open('/tmp/version',mode='r')
				newversion = file.read()
				file.close()

				file = open('/home/pi/quickpi/version',mode='r')
				currentversion = file.read()
				file.close()

				newversion = int(newversion.strip())
				currentversion = int(currentversion.strip())

				if newversion == currentversion:
					drawMenu("Auto update", "Already at " + str(currentversion), False)
					while True:
						pressed = waitForButton([LEFT_PIN], False)
						if pressed == LEFT_PIN:
							break
					continue

				drawMenu("Auto update", "Downloading " + str(newversion), False)
				time.sleep(1)

				result = os.system("curl -f " + UPDATEBASEURL + "quickpi.tar.gz --output /tmp/quickpi.tar.gz")

				if result != 0:
					drawMenu("Auto update", "Failed to download update", False)
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


				drawMenu("Auto update", "Sucess, restarting...", False)
				os.system("sudo reboot")
				while True:
					pressed = waitForButton([LEFT_PIN], False)
					if pressed == LEFT_PIN:
						break
					continue




draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)
device.display(oledimage)

