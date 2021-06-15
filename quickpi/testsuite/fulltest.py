from quickpi import *
import time
import RPi.GPIO as GPIO
import threading
import random
import os

def checkTest(value, name):
	if value:
		print("Test " + name + " passed")
		displayTextOled("Test " + name + " passed")
	else:
		print("Test " + name + " failed")
		displayTextOled("Test " + name + " failed")
	return [value, name]


def getAverageLightLevel(waittime):
	start = time.time()
	total = 0
	n = 0
	while time.time() - start < waittime:
		current = readADCADS1015(2)
		total = total + current
		n = n + 1

	return total/n

def getAverageSoundLevel(waittime):
	start = time.time()
	total = 0
	n = 0
	while time.time() - start < waittime:
		total = total + readSoundLevel(1)
		n = n + 1
	return total/n

def getIrReceiver(waittime, expected):
	start = time.time()
	while time.time() - start < waittime:
		if isButtonPressed(23) != expected:
			return False

	return True

#expected_i2c = [0x1d, 0x1e, 0x29,0x3c, 0x48, 0x68]
expected_i2c = [0x29,0x3c, 0x48, 0x68]

def listi2cDevices():
	#Set the screen pin high so that the screen can be detected
	RESET=21
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(RESET, GPIO.OUT)
	time.sleep(0.01)
	GPIO.output(RESET, 1)

	i2c_present = []
	for device in range(128):
		h = pi.i2c_open(1, device)
		try:
			pi.i2c_read_byte(h)
			i2c_present.append(device)
		except: 
			pass
		pi.i2c_close(h)

	return i2c_present


def testI2cDevices():
	global expected_i2c
#	has_base_devices =  listi2cDevices() == expected_i2c

	i2c_devices = listi2cDevices()

	for dev in expected_i2c:
		if dev not in i2c_devices:
			print("Didn't found all i2c  devices")
			return False

	if (0x1d in i2c_devices) and (0x1e in i2c_devices):
		print("Has standalone mag")
		return True # Already has an standalone  mag

	## We don't have a standalone magnetometer,check if this is a bmx160 with mag
	bus = smbus.SMBus(1)
	bmxchipid = bus.read_i2c_block_data(0x68, 0x00, 1)
	print("Bmx chip id is", bmxchipid, type(bmxchipid))
	print(bmxchipid[0] == 216)

	return bmxchipid[0] == 216



def testDistanceVL53l0x(up):
	print("Testing distance sensor VL53l0x")
	start = time.time()

	if up:
		displayTextOled("Unobstruct distance sensor")
		while True:
			distance = readDistanceVL53(0)
			if distance == 819.0:
				return True
	else:
		while time.time() - start < 0.5:
			distance = readDistanceVL53(0)
			if distance > 13:
				print("Distance > 130", distance)
				return False
	return True


def testAccelerometerBMI160():
	print("Testing accelerometer BMI160")
	start = time.time()
	while time.time() - start < 0.5:
		accel = readAccelBMI160()
		force = accel[0] + accel[1] + accel[2]
		if force < 8.0 and force > 12.0:
			return False

	return True


def testAccelerometerLSM303C():
	print("Testing accelerometer LSM303C")
	start = time.time()
	while time.time() - start < 0.5:
		accel = reaAccelerometerLSM303C()
		force = accel[0] + accel[1] + accel[2]
		#print(force)
		if force < 8.0 and force > 12.0:
			return False
	return True

def testLeds():
	print("Blinking Leds")
	for i in (27, 4, 17):
		print("Blinking led in " + str(i))
		start = time.time()
		while time.time() - start < 0.6:
			setLedState(i, 1)
			time.sleep(0.1)
			lighton = getAverageLightLevel(0.1)
			#print("On", lighton)
			setLedState(i, 0)
			time.sleep(0.1)
			lightoff = getAverageLightLevel(0.1)
			#print("Off", lightoff)
			#print("Diff", lighton - lightoff)
			if (lighton - lightoff) <= 4:
				print("Failed Diff", lighton - lightoff)
				return False

	return True

def testBuzzer():
	print("Blinking Buzzer")
	start = time.time()
	while time.time() - start < 1:
		changePassiveBuzzerState(12, 1)
		soundon = getAverageSoundLevel(0.5)
		changePassiveBuzzerState(12, 0)
		soundoff = getAverageSoundLevel(0.5)
		print("soundon", soundon, "soundoff", soundoff)
		if (soundon - soundoff) < 1:
			return False

	return True

def testButtons():
	print("Press all buttons")
	buttons_expected = [7, 8, 9, 10, 11, 26]
	buttons_already_pressed = []
	cleared = False

	while True:
		how_many_pressed = 0

		for button in buttons_expected:
			#print("Testing", button)
			if (isButtonPressed(button)): 
				button_pressed = button
				how_many_pressed = how_many_pressed + 1

		if how_many_pressed == 1:
			if button_pressed not in buttons_already_pressed:
				buttons_already_pressed.append(button_pressed)
				buttons_already_pressed.sort()
				print(buttons_already_pressed)

				if not cleared:
					fill(0)
					noStroke()
					drawRectangle(0, 0, 127, 31)

					stroke(1)
					drawCircle(17, 15, 6)
					drawCircle(28, 15, 6)
					drawCircle(17, 25, 6)
					drawCircle(17, 6, 6)
					drawCircle(6, 15, 6)
					drawCircle(50, 15, 6)

					fill(1)
					cleared = True

				if button_pressed == 7: #center
					drawCircle(17, 15, 6)
				elif button_pressed == 8: # right
					drawCircle(28, 15, 6)
				elif button_pressed == 9: # Down
					drawCircle(17, 25, 6)
				elif button_pressed == 10: # up
					drawCircle(17, 6, 6)
				elif button_pressed == 11: # Left
					drawCircle(6, 15, 6)
				elif button_pressed == 26:  #Button2
					drawCircle(50, 15, 6)

				noStroke()
				fill(0)
				drawRectangle(80, 0, 128 - 80, 31)
				fill(1)
				stroke(1)
				displayTextOledAtPos(str(len(buttons_already_pressed)) + "/6", 80, 5)

		if buttons_already_pressed == buttons_expected:
			return True
		time.sleep(0.1)

def testIRTransAndReceiver():
	print("Testing infrared emiter and receiver")
	start = time.time()
	while time.time() - start < 1:
		setInfraredState(22, 1)
		time.sleep(0.2)
		result = getIrReceiver(0.1, 0)
		if not result:
			return False
		setInfraredState(22, 0)
		time.sleep(0.2)
		result = getIrReceiver(0.1, 1)
		if not result:
			return False
	return True


def waitForBoard():
	global expected_i2c
	while True:
		i2c_devices = listi2cDevices()
		if len(i2c_devices) > 0:

			for dev in expected_i2c:
				if dev not in i2c_devices:
					print("Did not found", dev)
					time.sleep(0.5)
					break

			return

def waitForBoardRemoved(string):
	global expected_i2c
	fill = False
	while True:
		displayTextOled(string, "", fill)
		fill = not fill
		i2c_devices = listi2cDevices()
		if len(i2c_devices) == 0:
			return
		time.sleep(0.5)

def waitForBoardUp():
	uptimes = 0
	buzzerstate = False
	while True:
		buzzerstate = not buzzerstate
		changePassiveBuzzerState(12, buzzerstate)
		accel = readAccelBMI160()

		if accel == [0, 0, 0]:
			return False

		print("wait for up", accel)

		if (abs(accel[0]) <= 1.0 and
		    abs(accel[1]) <= 1.0 and
		    accel[2] <= 12.0 and accel[2] >= 8.0):
			uptimes = uptimes + 1
		else:
			uptimes = 0

		if uptimes > 4:
			changePassiveBuzzerState(12, False)
			return True

		time.sleep(0.2)

def waitForBoardDown():
	uptimes = 0
	buzzerstate = False
	while True:
		buzzerstate = not buzzerstate
		changePassiveBuzzerState(12, buzzerstate)
		accel = readAccelBMI160()

		if accel == [0, 0, 0]:
			return False

		if (abs(accel[0]) <= 1.0 and
		    abs(accel[1]) <= 1.0 and
		    accel[2] >= -12.0 and accel[2] <= -8.0):
			uptimes = uptimes + 1
			print("OK")
		else:
			uptimes = 0
			print("NOT OK")


		if uptimes > 4:
			changePassiveBuzzerState(12, False)
			return True

		time.sleep(0.2)

angles = [0, 0, 0]
calibration = [0, 0, 0]
stop_gyro = False

def testGyro():
	global angles
	print("Gyro", angles)
	xangle = abs(angles[0])
	yangle = abs(angles[1])

	if (xangle > 60 and xangle < 120) or (yangle > 60 and yangle < 120):
		return True

	return False

import statistics
def gyro_calibration_thread():
	global calibration

	calibrationsamples = 1000
	samples = 0

	while samples < calibrationsamples:
		values = readGyroBMI160()

		calibration[0] += values[0]
		calibration[1] += values[1]
		calibration[2] += values[2]
		samples += 1


	calibration[0] /= samples
	calibration[1] /= samples
	calibration[2] /= samples

def gyro_thread():
	global angles
	global calibration
	global stop_gyro

	lasttime = readGyroBMI160()[3]
	start = time.time()

	while True:
		if stop_gyro:
			break
		values = readGyroBMI160()

		dt = (values[3] - lasttime) * 3.9e-5
		lasttime = values[3]
#               print("DT = ", dt * 3.9e-5)

		angles[0] += (values[0] - calibration[0]) * dt
		angles[1] += (values[1] - calibration[1]) * dt
		angles[2] += (values[2] - calibration[2]) * dt

#               print(values)

#		if time.time() - start >= 0.5:
#			print(int(angles[0]), int(angles[1]), int(angles[2]))
#			start = time.time()


try:
	print("Waiting for board...")
	waitForBoard()
	displayTextOled("Board detected")
	time.sleep(2)

	displayTextOled("Press all buttons")
	checkTest(testButtons(), "buttons")

	threading.Thread(target=gyro_calibration_thread).start()


	result = checkTest(testIRTransAndReceiver(), "irtransrecv")

	if result[0]:
		result = checkTest(testAccelerometerLSM303C(), "accel-lsm303c")
	if result[0]:
		result = checkTest(testAccelerometerBMI160(), "accel-bmi160")
	if result[0]:
		result = checkTest(testI2cDevices(), "i2c-devices")

	if result[0]:
		displayTextOled("Put board face down")
		print("Waiting for board to be face down...")
		result = checkTest(waitForBoardDown(), "facedown")


	if result[0]:
		threading.Thread(target=gyro_thread).start()
		displayTextOled("", "")
		result = checkTest(testLeds(), "leds")

	if result[0]:
		result = checkTest(testDistanceVL53l0x(False), "distance")

	if result[0]:
		result = checkTest(testBuzzer(), "buzzer-mic")

	if result[0]:
		displayTextOled("Put board face up")
		print("Waiting for board to be face up...")
		result = checkTest(waitForBoardUp(), "boardup")

	if result[0]:
		result = checkTest(testDistanceVL53l0x(True), "distance")

	if result[0]:
		result = checkTest(testGyro(), "gyro")
	stop_gyro = True

	boardstatus = ""
	a = random.randrange(0, 255)
	b = a * 229
	b = b & 0xFF
	a = "%0.2X" % a
	b = "%0.2X" % b

	if result[0]:
		print("BOARD PASSED ALL TESTS")
#		displayTextOled("PASSED " + b + a)
		displayTextOled("ALL TESTS PASSED")
		boardstatus = "BOARD OK"
		#os.system("echo " + str(result[1]) + " > /mnt/data/" + a + b)

	else:
		print("BOARD failed ", result[1])
		displayTextOled("FAIL", result[1])
		boardstatus = "FAIL"
		#os.system("echo " + str(result[1]) + " > /mnt/data/" + a + b + "failed")

	#waitForBoardRemoved(boardstatus + " " + a + b)

except Exception as e:
	displayTextOled("FAIL")
	print(e)

changePassiveBuzzerState(12, False)
print("...")
time.sleep(3)
