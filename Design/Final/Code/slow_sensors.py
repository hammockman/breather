"""
Acquire sensor data.

Sensor nomenclature:

- type: flow (q), pressure (p), temp (t), humidity (h), O2 (o) 
- location: high pressure (isnpiration), low pressure (expiration)

jh, Mar 2020


Ra would like:

sensors = [
 {'name': 'Insp. pressure', 
'sensor_type': 'bmp085', 
'read_fn': None, 
'last_val': None, 
'units': 'Pa', 
'alarm_low': None, 
'alarm_high': None},
...]

can have derived channels in this list using e.g. read_fn = random().
can then fill in read_fn based on sensor type, and loop through this in read_all? 
can also pass this whole array back to main, and fill in MQTT stream with at least (name, value, unit, alarm_status) for each channel.

"""
import threading
from datetime import timedelta
import collections
import time

import Adafruit_DHT


# at the moment I'm hoping to simply grab everything once per control loop
# if it turns out sensors are slow/variable to read then this plan will change
__all__ = ["read_all_slow", "SlowSensors"] 

humidity_sensor_h = Adafruit_DHT.DHT11

def read_all_slow():

    #from time import sleep
    #sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info
    #from random import random

    h_h, t_h2 = Adafruit_DHT.read_retry(humidity_sensor_h, 4)

    return {
        't': time.time(),
        'h_h': h_h,
    }


class SlowSensorsThread(threading.Thread):
    def __init__(self, fs=0.5, daemon=True, maxnvalues=10, read_all_duration=2):
        threading.Thread.__init__(self)
        self.stopped = threading.Event()
        self.delay = timedelta(seconds=(max(0, 1./fs - read_all_duration)))
        print(self.delay)
        self.samples_recv = 0
        self.current_values = collections.deque(maxlen=maxnvalues)
        self.daemon = daemon # if set auto-terminate when main thread exits
        self.start()

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.delay.total_seconds()):
            self.current_values.append(read_all_slow())
            self.samples_recv += 1

            
if __name__=="__main__":
    #T = SensorsThread(fs=10, daemon=False)
    #print(read_bmp085_h(0x77))
    pass   
