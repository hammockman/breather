#!/usr/bin/python

import sys
sys.path.append('../')
from bmp085 import BMP085

import smbus
import time

bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) if you have a revision 2 board 
address = 0x77


def read_byte(adr):
    return bus.read_byte_data(address, adr)

def read_word(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    return val

def read_word_2c(adr):
    val = read_word(adr)
    if (val >= 0x8000):
        return -((0xffff - val) + 1)
    else:
        return val

def write_byte(adr, value):
    bus.write_byte_data(address, adr, value)

def twos_compliment(val):
    if (val >= 0x8000):
        return -((0xffff - val) + 1)
    else:
        return val

def get_word(array, index, twos):
    val = (array[index] << 8) + array[index+1]
    if twos:
        return twos_compliment(val)
    else:
        return val

calibration = bus.read_i2c_block_data(address, 0xAA, 22)

oss = 0

test = False

if test:
    ac1 =    408
    ac2 =    -72
    ac3 = -14383
    ac4 =  32741
    ac5 =  32757
    ac6 =  23153
    b1 =    6190
    b2 =       4
    mb =  -32768
    mc =   -8711
    md =    2868

    temp_raw = 27898 
    pressure_raw = 23843 

else:
    ac1 = get_word(calibration, 0, True)
    ac2 = get_word(calibration, 2, True)
    ac3 = get_word(calibration, 4, True)
    ac4 = get_word(calibration, 6, False)
    ac5 = get_word(calibration, 8, False)
    ac6 = get_word(calibration, 10, False)
    b1 =  get_word(calibration, 12, True)
    b2 =  get_word(calibration, 14, True)
    mb =  get_word(calibration, 16, True)
    mc =  get_word(calibration, 18, True)
    md =  get_word(calibration, 20, True)

    # Read raw temperature
    write_byte(0xF4, 0x2E)
    time.sleep(0.05)
    temp_raw = read_word_2c(0xF6)

    write_byte(0xF4, 0x34 + (oss << 6))
    time.sleep(0.05)
    pressure_raw = ((read_byte(0xF6) << 16) + (read_byte(0xF7) << 8) + (read_byte(0xF8)) ) >> (8-oss)


print("Raw temp:", temp_raw)
print("Raw pressure:", pressure_raw)


#Calculate temperature
x1 = ((temp_raw - ac6) * ac5) / 32768
x2 = (mc * 2048) / (x1 + md)
b5 = x1 + x2
t = (b5 + 8) / 16
print("Temp: ", t / 10.0, "degrees C")

b6 = b5 - 4000 ; print("b6 = ", b6)
x1 = int(b2 * int(b6 * b6) >> 12) >> 11 ; print("x1 = ",x1)
x2 = int(ac2 * b6) >> 11 ; print("b6x2 = ",x2)
x3 = x1 + x2 ; print("x3 = ",x3)
b3 = int((int(ac1 * 4 + x3) << oss) + 2) >> 2 ; print("b3 = ",b3)

x1 = int(ac3 * b6) >> 13 ; print("x1 = ",x1)
x2 = int(b1 * int(int(b6 * b6) >> 12)) >> 16 ; print("x2 = ",x2)
x3 = int((x1 + x2) + 2) >> 2 ; print("x3 = ",x3)
b4 = int(ac4 * (x3 + 32768)) >> 15 ; print("b4 = ",b4)
b7 = (pressure_raw - b3) * (int(50000) >> oss) ; print("b7 = ",b7)
if (b7 < 0x80000000):
    p = (b7 * 2) /b4 ; print("p = ",p)
else:
    p = (b7 / b4) *2 ; print("p1 = ",p)
x1 = (int(p) >> 8) * (int(p) >> 8) ; print("x1 = ",x1)
x1 = int(x1 * 3038) >> 16 ; print("x1 = ",x1)
x2 = int(-7357 * p) >> 16 ; print("x2 = ",x2)
p = p + (int(x1 + x2 + 3791) >> 4) ; print("pressure = ",p,"Pa")


pSensor = BMP085(address=0x77)
p_h, t_h = pSensor.read()
print("From sensors.py: %f Pa, %f degC " % (p_h, t_h))
