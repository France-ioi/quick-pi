import RPi.GPIO as GPIO
import pigpio
import time

quickpi_expected_i2c = [0x1d, 0x1e, 0x29,0x3c, 0x48, 0x68]
grove_expected_i2c = [0x04]
GPIO.setwarnings(False)

def listi2cDevices():
	#Set the screen pin high so that the screen can be detected
	RESET=21
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(RESET, GPIO.OUT)
	time.sleep(0.01)
	GPIO.output(RESET, 1)

	pi = pigpio.pi()

	i2c_present = []
	for device in range(128):
		h = pi.i2c_open(1, device)
		try:
			pi.i2c_read_byte(h)
			i2c_present.append(device)
		except:
			pass
		pi.i2c_close(h)

	pi.stop()

	return i2c_present

def detectBoard():
	i2cdevices = listi2cDevices()

	if i2cdevices == grove_expected_i2c:
		return "grove"
	elif i2cdevices == quickpi_expected_i2c:
		return "quickpi"
	elif len(i2cdevices) == 0:
		return "none"
	else:
		return "unknow"

