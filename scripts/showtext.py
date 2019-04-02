#!/usr/bin/python3
import RPi.GPIO as GPIO
import time
import smbus
import math
import pigpio 
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

button_interrupt_enabled = {}
button_was_pressed = {}
servo_object = {}
servo_last_value = {}

screenLine1 = None
screenLine2 = None

pi = pigpio.pi()

def displayText(line1, line2=""):
	global screenLine1
	global screenLine2
	
	if line1 == screenLine1 and line2 == screenLine2:
		return

	screenLine1 = line1
	screenLine2 = line2

	address = 0x3e
	bus = smbus.SMBus(1)

	bus.write_byte_data(address, 0x80, 0x01) #clear
	time.sleep(0.05)
	bus.write_byte_data(address, 0x80, 0x08 | 0x04) # display on, no cursor
	bus.write_byte_data(address, 0x80, 0x28) # two lines
	time.sleep(0.05)

	# This will allow arguments to be numbers
	line1 = str(line1)
	line2 = str(line2)

	count = 0
	for c in line1:
		bus.write_byte_data(address, 0x40, ord(c))
		count += 1
		if count == 16:
			break

	bus.write_byte_data(address, 0x80, 0xc0) # Next line
	count = 0
	for c in line2:
		bus.write_byte_data(address, 0x40, ord(c))
		count += 1
		if count == 16:
			break


if len(sys.argv) > 2:
   displayText(sys.argv[1], sys.argv[2])
else:
   displayText(sys.argv[1], "")
