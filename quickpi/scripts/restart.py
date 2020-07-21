# This script will restart the webserver
# and erase all locks if left and button 
# is pressed for 5 seconds
import RPi.GPIO as GPIO
import time
import os

GPIO.setmode(GPIO.BCM)

GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(7, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

start = 0
while True:
	# If left and button2 are pressed
	if GPIO.input(11) and GPIO.input(26):
		print("pressed")
		if start == 0:
			start = time.time()
	else:
		start = 0

	if start != 0 and time.time() - start > 5:
		print("restart")
		try:
			os.system("/home/pi/quickpi/scripts/runserver.sh")
			os.system("pkill -f quickpimenu.py")
			os.system("/usr/bin/python3 /home/pi/quickpi/scripts/quickpimenu.py &")
			start = 0
			time.sleep(15)
		except:
			pass


	time.sleep(0.5)
