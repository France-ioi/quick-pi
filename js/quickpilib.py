import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

def turnLedOn():
  GPIO.setup(14, GPIO.OUT)
  GPIO.output(14, GPIO.HIGH)

def turnLedOff():
  GPIO.setup(14, GPIO.OUT)
  GPIO.output(14, GPIO.LOW)



