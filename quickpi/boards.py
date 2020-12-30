import RPi.GPIO as GPIO
import pigpio
import time
import smbus

#quickpi_expected_i2c = [0x1d, 0x1e, 0x29, 0x3c, 0x48, 0x68] 
quickpi_expected_base_i2c = [0x29, 0x3c, 0x48, 0x68]

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
		return "grovepi"
	else:
		hasbasesensors = True
		for dev in quickpi_expected_base_i2c:
			if dev not in i2cdevices:
				hasbasesensors = False

		if hasbasesensors:
			if (0x1d in i2cdevices) and (0x1e in i2cdevices):
				return "quickpi" # This is a quickpi with standalone magnetometer

			else:
				bus = smbus.SMBus(1)
				chipid = bus.read_i2c_block_data(0x68, 0x00, 1)
				if chipid[0] == 216:
					return "quickpi" # This a quickpi with a bmx160 (accel, gyro and mag combo)


	if len(i2cdevices) == 0:
		return "none"
	else:
		return "unknow"
