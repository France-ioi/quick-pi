
try:
    sensorTable
except:
    sensorTable = []


import RPi.GPIO as GPIO
import time
import smbus
import math
import pigpio 
import threading

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

button_interrupt_enabled = {}
button_was_pressed = {}
servo_object = {}
servo_last_value = {}

DHT11_last_value = {}

distance_last_value = {}

passive_buzzer_last_value = {}

screenLine1 = None
screenLine2 = None

oleddisp = None
oledfont = None
oledimage = None
oleddraw = None
oledwidth = 128
oledheight = 32
oledautoupdate = True


vl53l0x = None

enabledBMI160 = False
enabledLSM303C = False

pi = pigpio.pi()

def nameToPin(name):
    for sensor in sensorTable:
        if sensor["name"] == name:
            return sensor["port"]

    return 0

def nameToDef(name, type):
    for sensor in sensorTable:
        if sensor["name"] == name:
            return sensor

    for sensor in sensorTable:
        if sensor["type"] == type:
            return sensor

    return None

def normalizePin(pin):
    returnpin = 0
    hadporttype = False

    pin = str(pin)

    if pin.isdigit():
        returnpin = pin
    elif len(pin) >= 2 and pin[0].isalpha() and pin[1:].isdigit():
        returnpin = pin[1:]
    else:
        returnpin = normalizePin(nameToPin(pin))

    return int(returnpin)


def cleanupPin(pin):
    pi.set_mode(pin, pigpio.INPUT)

def changePinState(pin, state):
    pin = normalizePin(pin)
    state = int(state)

    cleanupPin(pin)
    GPIO.setup(pin, GPIO.OUT)
    if state:
        GPIO.output(pin, GPIO.HIGH)
    else:
        GPIO.output(pin, GPIO.LOW)

def turnLedOn(pin=5):
	changePinState(pin, 1)

def turnLedOff(pin=5):
	changePinState(pin, 0)

def changeLedState(pin, state):
	changePinState(pin, state)

def toggleLedState(pin):
    pin = normalizePin(pin)

    GPIO.setup(pin, GPIO.OUT)
    if GPIO.input(pin):
        GPIO.output(pin, GPIO.LOW)
    else:
        GPIO.output(pin, GPIO.HIGH)

def buzzOn(pin):
  changePinState(pin, 1)

def buzzOff(pin):
  changePinState(pin, 0)

def magnetOn(pin):
  changePinState(pin, 1)

def magnetOff(pin):
  changePinState(pin, 0)

def buttonStateInPort(pin):
    pin = normalizePin(pin)

    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    return GPIO.input(pin)

def buttonState():
    return buttonStateInPort(22)

def waitForButton(pin):
    pin = normalizePin(pin)
    cleanupPin(pin)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    while not GPIO.input(pin):
        time.sleep(0.01)
    time.sleep(0.1) # debounce

def buttonWasPressedCallback(pin):
    button_was_pressed[pin] = 1

def buttonWasPressed(pin):
    pin = normalizePin(pin)
    init = False
    try:
        init = button_interrupt_enabled[pin]
    except:
        pass

    if not init:
        button_interrupt_enabled[pin] = True
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(pin, GPIO.FALLING, callback=buttonWasPressedCallback, bouncetime=300)

    wasPressed = 0

    try:
        wasPressed = button_was_pressed[pin]
        button_was_pressed[pin] = 0
    except:
            pass

    return wasPressed

def initVL53():
    global vl53l0x

    import board
    import busio
    import adafruit_vl53l0x

    try:
        i2c = busio.I2C(board.SCL, board.SDA)
        vl53l0x = adafruit_vl53l0x.VL53L0X(i2c)
    except:
        vl53l0x = None


def readDistanceVL53(pin):
    global vl53l0x
    distance = 0
    justinit = False

    if vl53l0x == None:
        initVL53()

        if vl53l0x is not None:
            justinit = True

    try:
        distance = vl53l0x.range / 10
    except:
        try:
            if not justinit:
                initVL53()
                distance = vl53l0x.range / 10
        except:
            pass

    return distance

usleep = lambda x: time.sleep(x / 1000000.0)

_TIMEOUT1 = 1000
_TIMEOUT2 = 10000

def readDistanceUltrasonic(pin):
    pin = normalizePin(pin)

    cleanupPin(pin)

    last_value = 0
    try:
        last_value = distance_last_value[pin]
    except:
        pass

    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    usleep(2)
    GPIO.output(pin, GPIO.HIGH)
    usleep(10)
    GPIO.output(pin, GPIO.LOW)

    GPIO.setup(pin, GPIO.IN)

    t0 = time.time()
    count = 0
    while count < _TIMEOUT1:
        if GPIO.input(pin):
            break
        count += 1
    if count >= _TIMEOUT1:
        return last_value

    t1 = time.time()
    count = 0
    while count < _TIMEOUT2:
        if not GPIO.input(pin):
            break
        count += 1
    if count >= _TIMEOUT2:
        return last_value

    t2 = time.time()

    dt = int((t1 - t0) * 1000000)
    if dt > 530:
        return last_value

    distance = ((t2 - t1) * 1000000 / 29 / 2)    # cm

    distance = round(distance, 1)

    distance_last_value[pin] = distance

    return distance

def initOLEDScreen():
    global oleddisp
    global oledfont
    global oledimage
    global oleddraw

    if oleddisp == None:
        from luma.core.interface.serial import i2c
        from luma.core.render import canvas
        from luma.oled.device import ssd1306
        from PIL import Image, ImageDraw, ImageFont

        RESET=21
        GPIO.setup(RESET, GPIO.OUT)
        GPIO.output(RESET, 0)
        time.sleep(0.01)
        GPIO.output(RESET, 1)

        serial = i2c(port=1, address=0x3C)
        oleddisp = ssd1306(serial, width=oledwidth, height=oledheight)
        oleddisp.cleanup = lambda _: True

        oledfont = ImageFont.load_default()
#        oledfont = ImageFont.truetype(font="tiny.ttf", size=8)
        oledimage = Image.new('1', (oledwidth, oledheight))
        oleddraw = ImageDraw.Draw(oledimage)

        oleddisp.display(oledimage)

# Address 0x3c
def displayTextOled(line1, line2="", background=True):
    global oleddisp
    global oledfont
    global oledimage
    global oleddraw
    
    initOLEDScreen()  

    # This will allow arguments to be numbers
    line1 = str(line1)
    line2 = str(line2)

    if background:
        fill = 0
    else:
        fill = 255

    oleddraw.rectangle((0, 0, oledwidth, oledheight), outline=0, fill=fill)

    if background:
        fill = 255
    else:
        fill = 0

    oleddraw.text((0, 0), line1, font=oledfont, fill=fill)
    oleddraw.text((0, 15), line2, font=oledfont, fill=fill)

    updateScreen()

def autoUpdate(autoupdate):
    global oledautoupdate

    oledautoupdate = bool(autoupdate)

def updateScreen():
    global oleddisp
    global oledimage

    oleddisp.display(oledimage)

fillcolor = 255
strokecolor = 255

def fill(color):
    global fillcolor

    if int(color) > 0:
        fillcolor = 255
    else:
        fillcolor = 0

def noFill():
    global fillcolor
    fillcolor = None

def stroke(color):
    global strokecolor

    if int(color) > 0:
        strokecolor = 255
    else:
        strokecolor = 0

def noStroke():
    global strokecolor
    strokecolor = None

def drawPoint(x, y):
    global oleddraw
    global strokecolor
    
    initOLEDScreen()

    oleddraw.point((x, y), fill=strokecolor)

    global oledautoupdate
    if oledautoupdate:
        updateScreen()

def drawText(x, y, text):
    global oleddisp
    global oledfont
    global oledimage
    global oleddraw
    
    initOLEDScreen()  

    # This will allow arguments to be numbers
    text = str(text)

    oleddraw.text((x, y), text, font=oledfont, fill=strokecolor)

    updateScreen()


def drawLine(x0, y0, x1, y1):
    global oleddraw
    global strokecolor

    initOLEDScreen()

    oleddraw.line((x0, y0, x1, y1), fill=strokecolor)

    global oledautoupdate
    if oledautoupdate:
        updateScreen()

def drawRectangle(x0, y0, width, height):
    global oleddraw
    global fillcolor
    global strokecolor

    initOLEDScreen()
    oleddraw.rectangle((x0, y0, x0 + width, y0 + height), fill=fillcolor, outline=strokecolor)

    global oledautoupdate
    if oledautoupdate:
        updateScreen()

def drawCircle(x0, y0, diameter):
    global oleddraw
    global fillcolor
    global strokecolor

    initOLEDScreen()

    radius = diameter / 2

    boundx0 = x0 - radius
    boundy0 = y0 - radius

    boundx1 = x0 + radius
    boundy1 = y0 + radius

    oleddraw.ellipse((boundx0, boundy0, boundx1, boundy1), fill=fillcolor, outline=strokecolor)

    global oledautoupdate
    if oledautoupdate:
        updateScreen()

def clearScreen():
    global oleddraw

    initOLEDScreen()

    oleddraw.rectangle((0, 0, oledwidth, oledheight), outline=0, fill=0)

    global oledautoupdate
    if oledautoupdate:
        updateScreen()

def displayText16x2(line1, line2=""):
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

def setServoAngle(pin, angle):
    pin = normalizePin(pin)
    angle = int(angle)

    pulsewidth = (angle * 11.11) + 500
    pi.set_servo_pulsewidth(pin, pulsewidth)

def readGrovePiADC(pin):
    pin = normalizePin(pin)

    reg = 0x30 + pin
    address = 0x04

    try:
        bus = smbus.SMBus(1)
        bus.write_byte(address, reg)
        return bus.read_word_data(address, reg)
    except:
        return 0


def sleep(sleep_time):
	sleep_time = float(sleep_time)
	time.sleep(sleep_time/1000)

def reportBlockValue(id, state):
    return state
    

class DHT11Result:
    'DHT11 sensor result returned by DHT11.read() method'

    ERR_NO_ERROR = 0
    ERR_MISSING_DATA = 1
    ERR_CRC = 2

    error_code = ERR_NO_ERROR
    temperature = -1
    humidity = -1

    def __init__(self, error_code, temperature, humidity):
        self.error_code = error_code
        self.temperature = temperature
        self.humidity = humidity

    def is_valid(self):
        return self.error_code == DHT11Result.ERR_NO_ERROR

# Taken from https://github.com/szazo/DHT11_Python
class DHT11:
    'DHT11 sensor reader class for Raspberry'

    __pin = 0

    def __init__(self, pin):
        self.__pin = pin

    def read(self):
        GPIO.setup(self.__pin, GPIO.OUT)

        # send initial high
        self.__send_and_sleep(GPIO.HIGH, 0.05)

        # pull down to low
        self.__send_and_sleep(GPIO.LOW, 0.02)

        # change to input using pull up
        GPIO.setup(self.__pin, GPIO.IN, GPIO.PUD_UP)

        # collect data into an array
        data = self.__collect_input()

        # parse lengths of all data pull up periods
        pull_up_lengths = self.__parse_data_pull_up_lengths(data)

        # if bit count mismatch, return error (4 byte data + 1 byte checksum)
        if len(pull_up_lengths) != 40:
            return DHT11Result(DHT11Result.ERR_MISSING_DATA, 0, 0)

        # calculate bits from lengths of the pull up periods
        bits = self.__calculate_bits(pull_up_lengths)

        # we have the bits, calculate bytes
        the_bytes = self.__bits_to_bytes(bits)

        # calculate checksum and check
        checksum = self.__calculate_checksum(the_bytes)
        if the_bytes[4] != checksum:
            return DHT11Result(DHT11Result.ERR_CRC, 0, 0)

        # ok, we have valid data, return it
        return DHT11Result(DHT11Result.ERR_NO_ERROR, the_bytes[2], the_bytes[0])

    def __send_and_sleep(self, output, sleep):
        GPIO.output(self.__pin, output)
        time.sleep(sleep)

    def __collect_input(self):
        # collect the data while unchanged found
        unchanged_count = 0

        # this is used to determine where is the end of the data
        max_unchanged_count = 100

        last = -1
        data = []
        while True:
            current = GPIO.input(self.__pin)
            data.append(current)
            if last != current:
                unchanged_count = 0
                last = current
            else:
                unchanged_count += 1
                if unchanged_count > max_unchanged_count:
                    break

        return data

    def __parse_data_pull_up_lengths(self, data):
        STATE_INIT_PULL_DOWN = 1
        STATE_INIT_PULL_UP = 2
        STATE_DATA_FIRST_PULL_DOWN = 3
        STATE_DATA_PULL_UP = 4
        STATE_DATA_PULL_DOWN = 5

        state = STATE_INIT_PULL_DOWN

        lengths = [] # will contain the lengths of data pull up periods
        current_length = 0 # will contain the length of the previous period

        for i in range(len(data)):

            current = data[i]
            current_length += 1

            if state == STATE_INIT_PULL_DOWN:
                if current == GPIO.LOW:
                    # ok, we got the initial pull down
                    state = STATE_INIT_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_INIT_PULL_UP:
                if current == GPIO.HIGH:
                    # ok, we got the initial pull up
                    state = STATE_DATA_FIRST_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_FIRST_PULL_DOWN:
                if current == GPIO.LOW:
                    # we have the initial pull down, the next will be the data pull up
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_UP:
                if current == GPIO.HIGH:
                    # data pulled up, the length of this pull up will determine whether it is 0 or 1
                    current_length = 0
                    state = STATE_DATA_PULL_DOWN
                    continue
                else:
                    continue
            if state == STATE_DATA_PULL_DOWN:
                if current == GPIO.LOW:
                    # pulled down, we store the length of the previous pull up period
                    lengths.append(current_length)
                    state = STATE_DATA_PULL_UP
                    continue
                else:
                    continue

        return lengths

    def __calculate_bits(self, pull_up_lengths):
        # find shortest and longest period
        shortest_pull_up = 1000
        longest_pull_up = 0

        for i in range(0, len(pull_up_lengths)):
            length = pull_up_lengths[i]
            if length < shortest_pull_up:
                shortest_pull_up = length
            if length > longest_pull_up:
                longest_pull_up = length

        # use the halfway to determine whether the period it is long or short
        halfway = shortest_pull_up + (longest_pull_up - shortest_pull_up) / 2
        bits = []

        for i in range(0, len(pull_up_lengths)):
            bit = False
            if pull_up_lengths[i] > halfway:
                bit = True
            bits.append(bit)

        return bits

    def __bits_to_bytes(self, bits):
        the_bytes = []
        byte = 0

        for i in range(0, len(bits)):
            byte = byte << 1
            if (bits[i]):
                byte = byte | 1
            else:
                byte = byte | 0
            if ((i + 1) % 8 == 0):
                the_bytes.append(byte)
                byte = 0

        return the_bytes

    def __calculate_checksum(self, the_bytes):
        return the_bytes[0] + the_bytes[1] + the_bytes[2] + the_bytes[3] & 255


def readTemperatureDHT11(pin):
    pin = normalizePin(pin)
    haveold = False

    try:
        lasttime = DHT11_last_value[pin]["time"]
        haveold = True
        if time.time() - lasttime < 2:
            return DHT11_last_value[pin]["temperature"]
    except:
        pass

       
    instance = DHT11(pin=pin)
    result = instance.read()
    if result.is_valid():
        DHT11_last_value[pin] = {
            "time": time.time(),
            "temperature": result.temperature,
            "humidity": result.humidity
        }
        return result.temperature
    elif haveold:
        return DHT11_last_value[pin]["temperature"] 

    return 0

def readHumidity(pin):
    pin = normalizePin(pin)
    haveold = False

    try:
        lasttime = DHT11_last_value[pin]["time"]
        haveold = True
        if time.time() - lasttime < 2:
            return DHT11_last_value[pin]["humidity"]
    except:
        pass

       
    instance = DHT11(pin=pin)
    result = instance.read()
    if result.is_valid():
        DHT11_last_value[pin] = {
            "time": time.time(),
            "temperature": result.temperature,
            "humidity": result.humidity
        }
        return result.humidity
    elif haveold:
        return DHT11_last_value[pin]["humidity"] 

    return 0

def currentTime():
    return time.time() * 1000


BMI160_DEVICE_ADDRESS = 0x68
BMI160_REGA_USR_CHIP_ID      = 0x00
BMI160_REGA_USR_ACC_CONF_ADDR     = 0x40
BMI160_REGA_USR_ACC_RANGE_ADDR    = 0x41
BMI160_REGA_USR_GYR_CONF_ADDR     = 0x42
BMI160_REGA_USR_GYR_RANGE_ADDR    = 0x43
BMI160_REGA_CMD_CMD_ADDR          =   0x7e
BMI160_REGA_CMD_EXT_MODE_ADDR     =   0x7f
BMI160_REGA_TEMPERATURE           = 0x20
CMD_SOFT_RESET_REG      = 0xb6
CMD_PMU_ACC_SUSPEND     = 0x10
CMD_PMU_ACC_NORMAL      = 0x11
CMD_PMU_ACC_LP1         = 0x12
CMD_PMU_ACC_LP2         = 0x13
CMD_PMU_GYRO_SUSPEND    = 0x14
CMD_PMU_GYRO_NORMAL     = 0x15
CMD_PMU_GYRO_FASTSTART  = 0x17

BMI160_USER_DATA_14_ADDR = 0X12 # accel x
BMI160_USER_DATA_15_ADDR = 0X13 # accel x
BMI160_USER_DATA_16_ADDR = 0X14 # accel y
BMI160_USER_DATA_17_ADDR = 0X15 # accel y
BMI160_USER_DATA_18_ADDR = 0X16 # accel z
BMI160_USER_DATA_19_ADDR = 0X17 # accel z

BMI160_USER_DATA_8_ADDR  = 0X0C
BMI160_USER_DATA_9_ADDR  = 0X0D
BMI160_USER_DATA_10_ADDR = 0X0E
BMI160_USER_DATA_11_ADDR = 0X0F
BMI160_USER_DATA_12_ADDR = 0X10
BMI160_USER_DATA_13_ADDR = 0X11

def initBMI160():
    bus = smbus.SMBus(1)
    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_USR_ACC_CONF_ADDR, 0x25)
    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_USR_ACC_RANGE_ADDR, 0x5)
    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_USR_GYR_CONF_ADDR, 0x26)
    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_USR_GYR_RANGE_ADDR, 0x1)

    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_CMD_CMD_ADDR, CMD_SOFT_RESET_REG)

    time.sleep(0.1)
    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_CMD_CMD_ADDR, CMD_PMU_ACC_NORMAL) # Enable ACCEL
    time.sleep(0.0038)
    bus.write_byte_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_CMD_CMD_ADDR, CMD_PMU_GYRO_NORMAL)  ## Enable Gyro
    time.sleep(0.080)

def readAccelBMI160():
    global enabledBMI160

    try:
        if not enabledBMI160:
            enabledBMI160 = True
            initBMI160()
        
        bus = smbus.SMBus(1)
        acc_value = bus.read_i2c_block_data(BMI160_DEVICE_ADDRESS, BMI160_USER_DATA_14_ADDR, 6)
        acc_x =  (acc_value[1] << 8) | acc_value[0]
        acc_y =  (acc_value[3] << 8) | acc_value[2]
        acc_z =  (acc_value[5] << 8) | acc_value[4]

        if acc_x & 0x8000 != 0:
            acc_x -= 1 << 16

        if acc_y & 0x8000 != 0:
            acc_y -= 1 << 16

        if acc_z & 0x8000 != 0:
            acc_z -= 1 << 16

        acc_x = float(acc_x)  / 16384.0;
        acc_y = float(acc_y)  / 16384.0;
        acc_z = float(acc_z) / 16384.0;

        return [round(acc_x, 1), round(acc_y, 1), round(acc_z, 1)]
    except:
        enabledBMI160 = False
        return [0, 0, 0]

def readAcceleration(axis):
    acceleration = readAccelBMI160()

    if axis.lower() == "x":
        return acceleration[0]
    elif axis.lower() == "y":
        return acceleration[1]
    elif axis.lower() == "z":
        return acceleration[2]

    return 0

def computeRotation(rotationType):
    acceleration = readAccelBMI160()
    zsign = 1

    if acceleration[2] < 0:
        zsign = -1

    if rotationType.lower() == "pitch":
        pitch = 180 * math.atan2 (acceleration[0], zsign * math.sqrt(acceleration[1]*acceleration[1] + acceleration[2]*acceleration[2]))/math.pi

        return int(pitch)
    elif rotationType.lower() == "roll":
        roll = 180 * math.atan2 (acceleration[1], zsign * math.sqrt(acceleration[0]*acceleration[0] + acceleration[2]*acceleration[2]))/math.pi

        return int(roll)

    return 0



def readGyroBMI160():
    global enabledBMI160

    try:
        if not enabledBMI160:
            enabledBMI160 = True
            initBMI160()

        bus = smbus.SMBus(1)
        value = bus.read_i2c_block_data(BMI160_DEVICE_ADDRESS, BMI160_USER_DATA_8_ADDR, 15)
        x =  (value[1] << 8) | value[0]
        y =  (value[3] << 8) | value[2]
        z =  (value[5] << 8) | value[4]

        time = (value[14] << 16) | (value[13] << 8) | value[12]


        if x & 0x8000 != 0:
            x -= 1 << 16

        if y & 0x8000 != 0:
            y -= 1 << 16

        if z & 0x8000 != 0:
            z -= 1 << 16

        x = float(x)  * 0.030517578125;
        y = float(y)  * 0.030517578125;
        z = float(z)  * 0.030517578125;
  
        return [x, y, z, time]
    except:
        enabledBMI160 = False
        return [0, 0, 0, 0]

def twos_comp(val, bits):
        # Calculate the 2s complement of int:val #
        if(val&(1<<(bits-1)) != 0):
                val = val - (1<<bits)
        return val

def readTemperatureBMI160(pin):
    global enabledBMI160

    try:
        if not enabledBMI160:
            enabledBMI160 = True
            initBMI160()

        bus = smbus.SMBus(1)
        temp_value = bus.read_i2c_block_data(BMI160_DEVICE_ADDRESS, BMI160_REGA_TEMPERATURE, 2)


        temp = twos_comp(temp_value[1] << 8 | temp_value[0], 16)

        temp = (temp * 0.0019073486328125) + 22.5

#        if temp & 0x8000:
            #temp = (23.0 - ((0x10000 - temp)/512.0));
#        else:
#            temp = ((temp/512.0) + 23.0);
    
        return temp
    except:
        enabledBMI160 = False
        return 0

ACC_I2C_ADDR = 0x1D
MAG_I2C_ADDR = 0x1E

CTRL_REG1               = 0x20
CTRL_REG2               = 0x21
CTRL_REG3               = 0x22
CTRL_REG4               = 0x23
CTRL_REG5               = 0x24

CTRL_REG1_A = 0x20
CTRL_REG2_A = 0x21
CTRL_REG3_A = 0x22
CTRL_REG4_A = 0x23
CTRL_REG5_A = 0x24
CTRL_REG6_A = 0x25
CTRL_REG7_A = 0x26

MAG_OUTX_L     = 0x28
MAG_OUTX_H     = 0x29
MAG_OUTY_L     = 0x2A
MAG_OUTY_H     = 0x2B
MAG_OUTZ_L     = 0x2C
MAG_OUTZ_H     = 0x2D


def initLSM303C():
    bus = smbus.SMBus(1)

    ## Magnetometer
    bus.write_byte_data(MAG_I2C_ADDR, CTRL_REG1, 0x7E) # X, Y High performace, Data rate 80hz
    bus.write_byte_data(MAG_I2C_ADDR, CTRL_REG4, 0x0C) # Z High performace
    bus.write_byte_data(MAG_I2C_ADDR, CTRL_REG5, 0x40)
    bus.write_byte_data(MAG_I2C_ADDR, CTRL_REG3, 0x00)

    ## Accelerometer
    bus.write_byte_data(ACC_I2C_ADDR, CTRL_REG5_A, 0x40)
    time.sleep(0.05)
    bus.write_byte_data(ACC_I2C_ADDR, CTRL_REG4_A, 0x0C)
    bus.write_byte_data(ACC_I2C_ADDR, CTRL_REG1_A, 0xBF) # High resolution, 100Hz output, enable all three axis


def readMagnetometerLSM303C():
    global enabledLSM303C

    try:
        if not enabledLSM303C:
            enabledLSM303C = True
            initLSM303C()

        bus = smbus.SMBus(1) 

        value = bus.read_i2c_block_data(MAG_I2C_ADDR, MAG_OUTX_L, 6)

        X =  twos_comp((value[1] << 8) | value[0], 16)
        Y =  twos_comp((value[3] << 8) | value[2], 16)
        Z =  twos_comp((value[5] << 8) | value[4], 16)

        X = round((X + 392.5) * 5000/5887, 0)
        Y = round((Y - 145.5) * 5000/5885, 0)
        Z =  round((Z + 3839)* 5000/6591, 0)

        return [X, Y, Z]
    except Exception as e:
        print(e)
        enabledLSM303C = False
        return [0, 0, 0]


def reaAccelerometerLSM303C():
    global enabledLSM303C

    try:
        if not enabledLSM303C:
            enabledLSM303C = True
            initLSM303C()

        bus = smbus.SMBus(1) 

        value = bus.read_i2c_block_data(ACC_I2C_ADDR, MAG_OUTX_L, 6)

        X =  twos_comp((value[1] << 8) | value[0], 16)
        Y =  twos_comp((value[3] << 8) | value[2], 16)
        Z =  twos_comp((value[5] << 8) | value[4], 16)

        X = round(X * 0.00059814453125 / 9.8, 3)
        Y = round(Y * 0.00059814453125 / 9.8, 3)
        Z =  round(Z * 0.00059814453125 / 9.8, 3)

        return [X, Y, Z]
    except:
        enabledLSM303C = False
        return [0, 0, 0]
 
def readMagneticForce(axis):
    maneticforce = readMagnetometerLSM303C()

    if axis.lower() == "x":
        return maneticforce[0]
    elif axis.lower() == "y":
        return maneticforce[1]
    elif axis.lower() == "z":
        return maneticforce[2]

    return 0


def readStick(pinup, pindown, pinleft, pinright, pincenter):
    pinup = normalizePin(pinup)
    pindown = normalizePin(pindown)
    pinleft = normalizePin(pinleft)
    pinright = normalizePin(pinright)
    pincenter = normalizePin(pincenter)


    GPIO.setup(pinup, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pindown, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pinleft, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pinright, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    GPIO.setup(pincenter, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    return [GPIO.input(pinup),
            GPIO.input(pindown),
            GPIO.input(pinleft),
            GPIO.input(pinright),
            GPIO.input(pincenter)]

def setInfraredState(pin, state):
    pin = normalizePin(pin)
    state = int(state)

    cleanupPin(pin)

    pi.set_mode(pin, pigpio.OUTPUT)

    pi.wave_clear()
    pi.wave_tx_stop()

    if state:
        wf = []

        wf.append(pigpio.pulse(1<<pin, 0, 13))
        wf.append(pigpio.pulse(0, 1<<pin, 13))

        pi.wave_add_generic(wf)

        a = pi.wave_create()

        pi.wave_send_repeat(a)

def changeActiveBuzzerState(pin, state):
    changePinState(pin, state)


def changePassiveBuzzerState(pin, state):
    pin = normalizePin(pin)
    laststate = 255

    try:
        laststate = passive_buzzer_last_value[pin]
    except:
        pass

    state = int(state)

    if state != laststate:
        passive_buzzer_last_value[pin] = state
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
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)


def readADCADS1015(pin, gain=1, raw=False):
    ADS1x15_CONFIG_GAIN = {
        2/3: 0x0000, # +/- 6.144V
        1:   0x0200, # +/- 4.096v
        2:   0x0400, # +/- 2.048v
        4:   0x0600, # +/- 1.024v
        8:   0x0800, # +/- 0.512v
        16:  0x0A00 # +/- 0.256v
    }

    ADS1x15_GAIN_MAX_VOLTAGE = {
        2/3: 6.144,
        1:   4.096,
        2:   2.048,
        4:   1.024,
        8:   0.512,
        16:  0.256
    }


    ADS1015_CONFIG_DR = {
        128:   0x0000,
        250:   0x0020,
        490:   0x0040,
        920:   0x0060,
        1600:  0x0080,
        2400:  0x00A0,
        3300:  0x00C0
    }

    ADS1x15_CONFIG_MUX_OFFSET      = 12
    ADS1x15_CONFIG_OS_SINGLE       = 0x8000
    ADS1x15_CONFIG_MODE_SINGLE      = 0x0100
    ADS1x15_CONFIG_COMP_QUE_DISABLE = 0x0003
    ADS1x15_POINTER_CONFIG = 0x01
    ADS1x15_POINTER_CONVERSION     = 0x00
    ADS1x15_CONFIG_MODE_CONTINUOUS  = 0x0000

    bus = smbus.SMBus(1)

    address = 0x48

    pin = normalizePin(pin)

    mux = pin + 0x04
    gainbits = ADS1x15_CONFIG_GAIN[gain]
    data_rate = 0x00C0 #3.3ksps

    config = ADS1x15_CONFIG_OS_SINGLE
    config |= (mux & 0x07) << ADS1x15_CONFIG_MUX_OFFSET
    config |= gainbits
    config |= ADS1x15_CONFIG_MODE_CONTINUOUS
    config |= data_rate
    config |= ADS1x15_CONFIG_COMP_QUE_DISABLE

    value = 0

    try:
        bus.write_i2c_block_data(address, ADS1x15_POINTER_CONFIG, [(config >> 8) & 0xFF, config & 0xFF])

        time.sleep(0.001)

        result = bus.read_i2c_block_data(address, ADS1x15_POINTER_CONVERSION, 2)

        value = twos_comp(result[0] << 8 | result[1], 16)

        if not raw:
            max = ADS1x15_GAIN_MAX_VOLTAGE[gain];

            # Normalize the value so that 0v is 0 and 3.3v is 999
            value = value / (32768. / max  * 3.3 / 1000.)

            if value < 0:
                value = 0

            if value > 999:
                value = 999
    except:
        pass

    return value


def readSoundLevel(pin):
    pin = normalizePin(pin)
    max = -25000
    min = 25000
    
    for i in range(50):
        val = int(readADCADS1015(pin, 8, True))

        if val > max:
            max = val

        if val < min:
            min = val

    return max - min        

adcHandler = [
    {
        "type": "grovepi", 
        "handler": readGrovePiADC
    },
    {
        "type": "ads1015",
        "handler": readADCADS1015
    }
]


def readADC(pin):
    try:
        for handler in adcHandler:
            if handler["type"] == currentADC:
                return handler["handler"](pin)
    except:
        pass

    return 0

def readTemperatureGroveAnalog(pin):
    B = 4275.
    R0 = 100000.

    val = readADC(pin)
    
    if val == 0:
        return 0

    r = 1000. / val - 1.
    r = R0 * r

    return round(1. / (math.log10(r / R0) / B + 1 / 298.15) - 273.15, 1)


def readRotaryAngle(pin):
	return int(readADC(pin) / 10)

def readSoundSensor(pin):
	return int(readADC(pin) / 10)

def readLightIntensity(pin):
	return int((readADC(pin) + 1)/ 10)
    
sensorHandler = [
    {
        "type": "screen",
        "subType": "oled128x32",
        "handler": displayTextOled
    },
    {
        "type": "screen",
        "subType": "16x2lcd",
        "handler": displayText16x2
    },
    {
        "type": "range",
        "subType": "vl53l0x",
        "handler": readDistanceVL53
    },
    {
        "type": "range",
        "subType": "ultrasonic",
        "handler": readDistanceUltrasonic
    },
    {
        "type": "temperature",
        "subType": "BMI160",
        "handler": readTemperatureBMI160
    },
    {
        "type": "temperature",
        "subType": "groveanalog",
        "handler": readTemperatureGroveAnalog
    },
    {
        "type": "temperature",
        "subType": "DHT11",
        "handler": readTemperatureDHT11
    },
    {
        "type": "buzzer",
        "subType": "passive",
        "handler": changePassiveBuzzerState
    },
    {
        "type": "buzzer",
        "subType": "active",
        "handler": changeActiveBuzzerState
    },
]

def nameToHandler(name, type):
    sensor =  nameToDef(name, "range")

    if sensor is not None:
        for handler in sensorHandler:
            if handler["type"] == type and "subType" in sensor and handler["subType"] == sensor["subType"]:
                return [sensor, handler["handler"]]
    return None
        

def readDistance(name):
    ret =  nameToHandler(name, "range")

    if ret is not None:
        sensor = ret[0]
        handler = ret[1]

        return handler(name)
    
    return 0


def displayText(name, line1, line2=""):
    ret =  nameToHandler(name, "screen")

    if ret is not None:
        sensor = ret[0]
        handler = ret[1]

        return handler(line1, line2)

def readTemperature(name):
    ret =  nameToHandler(name, "temperature")

    if ret is not None:
        sensor = ret[0]
        handler = ret[1]

        return round(handler(name), 1)
    
    return 0

def setBuzzerState(name, state):
    ret =  nameToHandler(name, "buzzer")

    if ret is not None:
        sensor = ret[0]
        handler = ret[1]

        return handler(name, state)
    
    return 0

def setBuzzerAudioOutput(value):
    if value:
        pi.set_mode(12, pigpio.ALT0) # 12 is PWM0
    else:
        pi.set_mode(12, pigpio.ALT1) # 12 normal


def getBuzzerAudioOutput():
    if pi.get_mode(12) == pigpio.ALT0:
        return 1

    return 0
