import RPi.GPIO as GPIO
import pigpio

def docleanup():
	try:
		pi = pigpio.pi()
		pi.set_mode(5, pigpio.INPUT)
		pi.set_mode(16, pigpio.INPUT)
		pi.set_mode(22, pigpio.INPUT)
		pi.set_mode(24, pigpio.INPUT)
		pi.set_mode(26, pigpio.INPUT)

		pi.stop()

		GPIO.setmode(GPIO.BCM)
		GPIO.setup(5, GPIO.IN)
		GPIO.setup(16, GPIO.IN)
		GPIO.setup(22, GPIO.IN)
		GPIO.setup(24, GPIO.IN)
		GPIO.setup(26, GPIO.IN)
	except:
		pass

