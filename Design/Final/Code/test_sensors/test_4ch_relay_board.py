#!/usr/bin/python


from gpiozero import LED
from time import sleep

led = LED(17)

fs = 50

while 1:
  led.on()
  print(led.is_lit)
  sleep(1/(2*fs))
  led.off()
  print(led.is_lit)
  sleep(1/(2*fs))

