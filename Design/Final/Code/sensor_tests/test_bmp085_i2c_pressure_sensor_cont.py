#!/usr/bin/python

import sys
sys.path.append('../')
import time

from bmp085 import BMP085

t_sec = time.localtime().tm_sec
t_sec_old = t_sec
n = 0
pSensor = BMP085(address=0x77)
while 1:
  t_sec = time.localtime().tm_sec
  p_h, t_h = pSensor.read()
  n = n + 1
  if t_sec != t_sec_old:
    print("Time: %d s, fs=%f, p=%f Pa, T=%f degC " % (t_sec, n, p_h, t_h))
    t_sec_old = t_sec
    n = 0
