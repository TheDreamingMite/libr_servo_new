# control_servo.py

import keyboard as kb
import smbus

import logging
import time
import math


#constants for Control_servo:

# Configure min and max servo pulse lengths
servo_min = 130 # Min pulse length out of 4096 / 150/112
servo_max = 510 # Max pulse length out of 4096 / 600/492

UP = 'w'
DOWN = 's'
LEFT = 'a'
RIGHT = 'd'

UP_STOP = 510
DOWN_STOP = 130
LEFT_STOP = 130
RIGHT_STOP = 510

# Based on Adafruit Lib:
# https://github.com/adafruit/Adafruit_Python_PCA9685/blob/master/Adafruit_PCA9685/PCA9685.py

# Default address:
PCA9685_ADDRESS    = 0x40

# Registers/etc:
MODE1              = 0x00
MODE2              = 0x01
SUBADR1            = 0x02
SUBADR2            = 0x03
SUBADR3            = 0x04
PRESCALE           = 0xFE
LED0_ON_L          = 0x06
LED0_ON_H          = 0x07
LED0_OFF_L         = 0x08
LED0_OFF_H         = 0x09
ALL_LED_ON_L       = 0xFA
ALL_LED_ON_H       = 0xFB
ALL_LED_OFF_L      = 0xFC
ALL_LED_OFF_H      = 0xFD

# Bits:
RESTART            = 0x80
SLEEP              = 0x10
ALLCALL            = 0x01
INVRT              = 0x10
OUTDRV             = 0x04

# Channels
CHANNEL00          = 0x00
CHANNEL01          = 0x01
CHANNEL02          = 0x02
CHANNEL03          = 0x03
CHANNEL04          = 0x04
CHANNEL05          = 0x05
CHANNEL06          = 0x06
CHANNEL07          = 0x07
CHANNEL08          = 0x08
CHANNEL09          = 0x09
CHANNEL10          = 0x0A
CHANNEL11          = 0x0B
CHANNEL12          = 0x0C
CHANNEL13          = 0x0D
CHANNEL14          = 0x0E
CHANNEL15          = 0x0F

class PCA9685(object):
    def __init__(self, i2cBus, address=PCA9685_ADDRESS):
        self.i2cBus = i2cBus
        self.address = address
        self.begin()

    def begin(self):
        """Initialize device"""
        self.set_all_pwm(0, 0)
        self.i2cBus.write_byte_data(self.address, MODE2, OUTDRV)
        self.i2cBus.write_byte_data(self.address, MODE1, ALLCALL)
        time.sleep(0.005)                                         # wait for oscillator
        mode1 = self.i2cBus.read_byte_data(self.address, MODE1)
        mode1 = mode1 & ~SLEEP                                    # wake up (reset sleep)
        self.i2cBus.write_byte_data(self.address, MODE1, mode1)
        time.sleep(0.005)                                         # wait for oscillator

    def reset(self):
        self.i2cBus.write_byte_data(self.address, MODE1, RESTART)
        time.sleep(0.01)

    def set_address(self, address):
        """Sets device address."""
        self.address = address

    def set_i2c_bus(self, i2cBus):
        """Sets I2C Bus."""
        self.i2cBus = i2cBus

    def set_pwm(self, channel, on, off):
        """Sets a single PWM channel."""
        self.i2cBus.write_byte_data(self.address, LED0_ON_L + 4 * channel, on & 0xFF)
        self.i2cBus.write_byte_data(self.address, LED0_ON_H + 4 * channel, on >> 8)
        self.i2cBus.write_byte_data(self.address, LED0_OFF_L + 4 * channel, off & 0xFF)
        self.i2cBus.write_byte_data(self.address, LED0_OFF_H + 4 * channel, off >> 8)

    def set_all_pwm(self, on, off):
        """Sets all PWM channels."""
        self.i2cBus.write_byte_data(self.address, ALL_LED_ON_L, on & 0xFF)
        self.i2cBus.write_byte_data(self.address, ALL_LED_ON_H, on >> 8)
        self.i2cBus.write_byte_data(self.address, ALL_LED_OFF_L, off & 0xFF)
        self.i2cBus.write_byte_data(self.address, ALL_LED_OFF_H, off >> 8)

    def set_pwm_freq(self, freq_hz):
        """Set the PWM frequency to the provided value in hertz."""
        prescaleval = 25000000.0                                  # 25MHz
        prescaleval /= 4096.0                                     # 12-bit
        prescaleval /= float(freq_hz)
        prescaleval -= 1.0
        prescale = int(math.floor(prescaleval + 0.5))
        oldmode = self.i2cBus.read_byte_data(self.address, MODE1)
        newmode = (oldmode & 0x7F) | 0x10                         # sleep
        self.i2cBus.write_byte_data(self.address, MODE1, newmode) # go to sleep
        self.i2cBus.write_byte_data(self.address, PRESCALE, prescale)
        self.i2cBus.write_byte_data(self.address, MODE1, oldmode)
        time.sleep(0.005)
        self.i2cBus.write_byte_data(self.address, MODE1, oldmode | 0x80)

    def __enter__(self):
        return self
    def __exit__(self, exception_type, exception_value, traceback):
        self.reset()

def map(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min + 1) / (in_max - in_min + 1) + out_min

class ServoPCA9685:
    def __init__(self, pca9685, channel):
        self.pca9685 = pca9685
        self.channel = channel
        self.set_pwm_freq(50)
        self.set_pulse(300)

    def set_pwm_freq(self, freq=50):
        self.pca9685.set_pwm_freq(freq)
        time.sleep(0.005)

    def set_angle(self, angle):
        self.set_pulse(map(angle, 0, 180, servo_min, servo_max))

    def set_pulse(self, pulse):
        if pulse >= servo_min and pulse <= servo_max:
            self.pca9685.set_pwm(self.channel, 0, pulse)
            time.sleep(0.005)

    def disable(self):
        self.pca9685.set_pwm(self.channel, 0, 0)
        time.sleep(0.005)

i2cbus = smbus.SMBus(0)
pca = PCA9685(i2cbus)
s0 = ServoPCA9685(pca, CHANNEL00)
s1 = ServoPCA9685(pca, CHANNEL01)

# Settings for joystick
address_joy = 0x48
bus_joy = smbus.SMBus(1)

class Control_servo(object):
    def __init__(self, pulsex = 130, pulsey = 130):
        self.pulsex = pulsex
        self.pulsey = pulsey

    def setX(self, x):
        self.pulsex = x

    def setY(self, y):
        self.pulsey = y

    def getX(self):
        return self.pulsex

    def getY(self):
        return self.pulsey
    def run_key(self, delta = 15):
        while True:
            if kb.is_pressed(UP) and self.pulsey + delta <= UP_STOP:
                self.pulsey += delta
            if kb.is_pressed(DOWN) and self.pulsey - delta >= DOWN_STOP:
                self.pulsey -= delta
            if kb.is_pressed(LEFT) and self.pulsex - delta >= LEFT_STOP:
                self.pulsex -= delta
            if kb.is_pressed(RIGHT) and self.pulsex + delta <= RIGHT_STOP:
                self.pulsex += delta

            s0.set_pulse(self.pulsex)
            s1.set_pulse(self.pulsey)

            # print(f"pulsex: {self.pulsex}, pulsey: {self.pulsey}")
            # print(self.pulsex)
            # print(self.pulsey)
    def run_joystik(self, delta = 15):
        while(True):
            bus_joy.write_byte(address_joy, 0x40)
            value_BUT = bus_joy.read_byte(address_joy)

            bus_joy.write_byte(address_joy, 0x41)
            value_Y = bus_joy.read_byte(address_joy)

            bus_joy.write_byte(address_joy, 0x42)
            value_X = bus_joy.read_byte(address_joy)

            if(value_BUT > 0):
                value_BUT = "Button is OFF"
            else:
                value_BUT = "Button is ON"
# center: 194 and 199 MAX,MIN: (208, 10),(212,13)
            if value_Y > 207 and self.pulsey + delta <= UP_STOP:
                self.pulsey += delta
            if value_Y < 70 and self.pulsey - delta >= DOWN_STOP:
                self.pulsey -= delta
            if value_X > 202 and self.pulsex - delta >= LEFT_STOP:
                self.pulsex -= delta
            if value_X < 70 and self.pulsex + delta <= RIGHT_STOP:
                self.pulsex += delta

            s0.set_pulse(self.pulsex)
            s1.set_pulse(self.pulsey)
                
            print(str(value_X) + "\t" + str(value_Y) + "\t" + str(value_BUT)) 
            # print(f"pulsex: {self.pulsex}, pulsey: {self.pulsey}")
            # print(self.pulsex)
            # print(self.pulsey)
    def run_buttons(self, delta = 15, button_pin_UP = 11, button_pin_DOWN = 22, button_pin_LEFT = 23, button_pin_RIGHT = 24):
        GPIO.setmode(GPIO.BOARD)

        GPIO.setup(self.button_pin_UP, GPIO.IN)
        GPIO.setup(self.button_pin_DOWN, GPIO.IN)
        GPIO.setup(self.button_pin_RIGHT, GPIO.IN)
        GPIO.setup(self.button_pin_LEFT, GPIO.IN)

        size_buf = 20
        
        buffer_UP = [1] * size_buf
        pressed_UP = [0] * size_buf
        
        buffer_DOWN = [1] * size_buf
        pressed_DOWN = [0] * size_buf
        
        buffer_RIGHT = [1] * size_buf
        pressed_RIGHT = [0] * size_buf
        
        buffer_LEFT = [1] * size_buf
        pressed_LEFT = [0] * size_buf
        while True:
            button_state_UP = GPIO.input(self.button_pin_UP)
            buffer_UP.pop(0)
            buffer_UP.append(button_state_UP)
            
            button_state_DOWN = GPIO.input(self.button_pin_DOWN)
            buffer_DOWN.pop(0)
            buffer_DOWN.append(button_state_DOWN)

            button_state_RIGHT = GPIO.input(self.button_pin_RIGHT)
            buffer_RIGHT.pop(0)
            buffer_RIGHT.append(button_state_RIGHT)
            
            button_state_LEFT = GPIO.input(self.button_pin_LEFT)
            buffer_LEFT.pop(0)
            buffer_LEFT.append(button_state_LEFT)
            
            # print(button_state_UP)
            # print(button_state_DOWN)
            # print(button_state_RIGHT)
            # print(button_state_LEFT)
            
            if button_state_UP == pressed_UP and self.pulsey + delta <= UP_STOP:
                self.pulsey += delta
                # print("UP +")
            if button_state_DOWN == pressed_DOWN and self.pulsey - delta >= DOWN_STOP:
                self.pulsey += delta
                # print("DOWN +")

            if button_state_RIGHT == pressed_RIGHT and self.pulsex + delta <= RIGHT_STOP:
                self.pulsex += delta
                # print("RIGHT +")

            if button_state_LEFT == pressed_LEFT and self.pulsex - delta >= LEFT_STOP:
                self.pulsex -= delta
                # print("LEFT +")

            s0.set_pulse(self.pulsex)
            s1.set_pulse(self.pulsey)

            # print(f"pulsex: {self.pulsex}, pulsey: {self.pulsey}")
            # print(self.pulsex)
            # print(self.pulsey)

    def start(self):
        print("Start listening keyboard...")
