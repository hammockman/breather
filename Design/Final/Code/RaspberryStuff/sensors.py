"""
Acquire sensor data.

Sensor nomenclature:

- type: flow (q), pressure (p), temp (t), humidity (h), O2 (o) 
- location: high pressure (isnpiration), low pressure (expiration)

jh, Mar 2020
"""
import threading
from datetime import timedelta

# at the moment I'm hoping to simply grab everything once per control loop
# if it turns out sensors are slow/variable to read then this plan will change
__all__ = ["read_all", "Sensors"] 


def read_all():

    from time import sleep
    sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info
    from random import random
    
    return {
        'q_h':random(),
        'q_l':None,
        'p_h':None, 
        'p_l':None,
        't_h':None,
        't_l':None,
        'h_h':None,
        'h_l':None,
        'o_h':None,
        'o_l':None,
    }


class SensorsThread(threading.Thread):
    def __init__(self, fs=10):
        threading.Thread.__init__(self)
        self.stopped = threading.Event()
        self.delay = timedelta(seconds=1./fs)
        self.samples_recv = 0
        self.current_values = None
        self.daemon = True # set this to terminate when main program exits
        self.start()

        
    def stop(self):
        self.stopped.set()
        self.join()

        
    def run(self):
        while not self.stopped.wait(self.delay.total_seconds()):
            self.current_values = read_all()
            self.samples_recv += 1

            
if __name__=="__main__":
    T = SensorsThread(fs=10)
        
