#!/usr/bin/env python3
import time
from smbus import SMBus
bus = SMBus(1)

# this device should be address 0x48
def readChannel(params):
  global bus
  bus.write_byte(0x48, params & 0x03) # select the channel
  bus.write_byte(0x48, 0) # give it time to convert
  return bus.read_byte(0x48)

def analogOut(out):
  global bus
  bus.write_byte(0x48, 0x80)
  bus.write_byte(0x48, int(out) & 0xFF)
  bus.write_byte(0x48, 0x00)

def readAll():
  global bus
  bus.write_byte(0x48, 0x04) # auto-increment command
  data = []
  for _ in range(4):
    data.append(bus.read_byte(0x48))
    return data
  
while(True):
  #print('all values are:')
  print(readAll())
  #print('channel 1 is:')
  print(readChannel(1))
  #print('check AOUT, should be about 2.5v')
  #print(analogOut(255 / 2))
  time.sleep(.05)
