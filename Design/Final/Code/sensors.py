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

try:
    from smbus import SMBus
except:
    from fakesmbus import SMBus
bus = SMBus(1)

# at the moment I'm hoping to simply grab everything once per control loop
# if it turns out sensors are slow/variable to read then this plan will change
__all__ = ["read_all", "Sensors"] 

bmp085_h = BMP085(bus=1, address=0x77)
bmp085_l = BMP085(bus=4, address=0x77)

# this device should be address 0x48
def read_ai0():
  bus.write_byte(0x48, 0 & 0x03) # select the channel
  bus.write_byte(0x48, 0) # give it time to convert
  return bus.read_byte(0x48)

def read_all():

    #from time import sleep
    #sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info
    #from random import random


    p_h, t_h = bmp085_h.read()
    p_l, t_l = bmp085_l.read()
    q_h = read_ai0() - 31 # 31 seems to be zero flow.
    
    return {
        't': time.time(),
        'q_h': q_h,
        'q_l': None,
        'p_h': p_h, 
        'p_l': p_l,
        't_h': t_h,
        't_l': t_l,
        'o_h': None,
        'o_l': None,
    }


class SensorsThread(threading.Thread):
    def __init__(self, fs=10, daemon=True, maxnvalues=100, read_all_duration=0.11, **kwargs):
        threading.Thread.__init__(self)
        self.p_set_point = 0
        self.rl_p_set_point = RateLimiter(-20, 20, 1/30)
        #self.pidf = PIDF(0.4, 0, 0, 0.05)
        self.pidf = PIDF(0.1, 0, 0, 0.03)
        # 2 Hz.
        self.lpf_p = LPF([0.00355661, 0.00711322, 0.00355661], [ 1., -1.78994555,0.80417199])
        # 5 Hz at fs=15
        #[0.05628602, 0.16885807, 0.16885807, 0.05628602]
        self.i_valve_id = 0
        self.e_valve_id = 2
        self.stopped = threading.Event()
        self.delay = timedelta(seconds=(max(0, 1./fs - read_all_duration)))
        print(self.delay)
        self.samples_recv = 0
        self.current_values = collections.deque(maxlen=maxnvalues)
        self.daemon = daemon # if set auto-terminate when main thread exits
        self.valves = [LED(17), LED(18), LED(22)]
        self.ie = None # for tracking inspiration/expiration
        for k,v in kwargs.items():
            setattr(self, k, v) # e.g. installed_flow_meters
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
            current_val = read_all()
            current_val['ie'] = self.ie # not needed, but maybe helpful for debugging

            # integrate tidal volume
            if len(self.current_values)>1: # catch the case when no data yet acquired
                dt = current_val['t'] - self.current_values[-1]['t']
                dtv = (current_val['q_h'] + self.current_values[-1]['q_h'])/2 * dt
                if self.installed_flow_meters=='I':
                    if self.ie>0: # inspiration
                        current_val['tv_h'] = self.current_values[-1]['tv_h'] + dtv
                    else:
                        current_val['tv_h'] = 0 # FIXME: patient exhales instantaneously!!!
                elif self.installed_flow_meters=='E':
                    if self.ie>0: # inspiration
                        # start simple with just -ve 
                        current_val['tv_h'] = 0 # FIXME: patient INHALES instantaneously!!!
                    else:
                        current_val['tv_h'] = self.current_values[-1]['tv_h'] - dtv
                else:
                    raise ValueError('Unknown value for installed_flow_meters=%s % self.installed_flow_meters')
            else:
                current_val['tv_h'] = 0 # default value
            
            self.current_values.append(current_val)
            self.samples_recv += 1

            #p_set_point_rl = self.rl_p_set_point.update(self.p_set_point)
            p_set_point_rl = self.p_set_point
            #print(p_set_point_rl)
            #p_h = self.lpf_p.update(self.current_values[-1]['p_h'])
            p_h = self.current_values[-1]['p_h']
            u = self.pidf.calc_output(p_h, p_set_point_rl)
            #print('%2.0f\t%2.0f\t%2.0f' % (self.p_set_point, self.current_values[-1]['p_h'] - 988, u))
            #print(' '*2*int(p_set_point_rl) + 's')
            #print(' '*2*int(self.current_values[-1]['p_h']) + 'p')
            #print(' '*int(u) + 'u')
            # Hacking completely:
            if self.ie>0:
                self.send_to_valve(self.i_valve_id, u)
                self.valves[self.e_valve_id].off()
            else:
                self.send_to_valve(self.i_valve_id, 0)
                self.valves[self.e_valve_id].on()
            #if self.samples_recv%(selfs.current_values.maxlen//2)==0:
            #    import pandas as pd
            #    print(pd.DataFrame(self.current_values)['t'].diff())

            
if __name__=="__main__":
    #T = SensorsThread(fs=10, daemon=False)
    print(read_bmp085_h(0x77))
        
