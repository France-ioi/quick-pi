#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import smbus
import sys

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

screenwidth = 128
screenheight = 32

RESET=21
GPIO.setmode(GPIO.BCM)
GPIO.setup(RESET, GPIO.OUT)
GPIO.output(RESET, 0)
time.sleep(0.01)
GPIO.output(RESET, 1)

serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, width=128, height=32)
device.cleanup = lambda _: True


oledimage = Image.new('1', (128, 32))
draw = ImageDraw.Draw(oledimage)
oledfont = ImageFont.load_default()

def displayText(line1, line2, line3):
	draw.rectangle((0, 0, screenwidth - 1, screenheight - 1), outline=0, fill=0)
	draw.text((0, 0), line1, font=oledfont, fill=255)
	draw.text((0, 11), line2, font=oledfont, fill=255)
	draw.text((0, 21), line3, font=oledfont, fill=255)

	device.display(oledimage)



if len(sys.argv) > 2:
   displayText(sys.argv[1], sys.argv[2], "")
else:
   displayText("", sys.argv[1], "")
