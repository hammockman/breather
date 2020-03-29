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

try:
    from gpiozero import LED
except:
    from fakegpiozero import LED

from bmp085 import BMP085
from pidf import PIDF
from lpf import LPF
from rate_limiter import RateLimiter

# at the moment I'm hoping to simply grab everything once per control loop
# if it turns out sensors are slow/variable to read then this plan will change
__all__ = ["read_all", "Sensors"] 

bmp085 = BMP085(address=0x77)

def read_all():

    #from time import sleep
    #sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info
    #from random import random


    p_h, t_h = bmp085.read()
    
    return {
        't': time.time(),
        'q_h':None,
        'q_l':None,
        'p_h':p_h, 
        'p_l':None,
        't_h':t_h,
        't_l':None,
        'h_h':None,
        'h_l':None,
        'o_h':None,
        'o_l':None,
    }


class SensorsThread(threading.Thread):
    def __init__(self, fs=10, daemon=True, maxnvalues=100, read_all_duration=0.11):
        threading.Thread.__init__(self)
        self.p_set_point = 0
        self.rl_p_set_point = RateLimiter(5, 10, 1/50)
        self.pidf = PIDF(0.5, 0, 0, 0.05)
        # 2 Hz.
        self.lpf_p = LPF([0.00355661, 0.00711322, 0.00355661], [ 1., -1.78994555,0.80417199])
        self.i_valve_id = 0
        self.e_valve_id = 2
        self.stopped = threading.Event()
        self.delay = timedelta(seconds=(max(0, 1./fs - read_all_duration)))
        print(self.delay)
        self.samples_recv = 0
        self.current_values = collections.deque(maxlen=maxnvalues)
        self.daemon = daemon # if set auto-terminate when main thread exits
        self.valves = [LED(17), LED(18), LED(22)]
        self.start()

    def stop(self):
        self.stopped.set()
        self.join()

    def send_to_valve(self, valve_id, signal):
        # Make some sort of PWM
        if signal > 0:
            self.valves[valve_id].on()
        else:
            self.valves[valve_id].off()
        
        
    def run(self):
        while not self.stopped.wait(self.delay.total_seconds()):
            self.current_values.append(read_all())
            self.samples_recv += 1
            #p_set_point_rl = self.rl_p_set_point.update(self.p_set_point)
            p_set_point_rl = self.p_set_point
            #p_h = self.lpf_p.update(self.current_values[-1]['p_h'])
            p_h = self.current_values[-1]['p_h']
            u = self.pidf.calc_output(p_h, p_set_point_rl)
            #print('%2.0f\t%2.0f\t%2.0f' % (self.p_set_point, self.current_values[-1]['p_h'] - 988, u))
            #print(' '*2*int(self.p_set_point) + 's')
            #print(' '*2*int(self.current_values[-1]['p_h']) + 'p')
            #print(' '*int(u) + 'u')
            self.send_to_valve(self.i_valve_id, u)
            # Hacking completely:
            if self.p_set_point < 10:
                self.valves[self.e_valve_id].on()
            else:
                self.valves[self.e_valve_id].off()
            #if self.samples_recv%(selfs.current_values.maxlen//2)==0:
            #    import pandas as pd
            #    print(pd.DataFrame(self.current_values)['t'].diff())

            
if __name__=="__main__":
    #T = SensorsThread(fs=10, daemon=False)
    print(read_bmp085(0x77))
        
