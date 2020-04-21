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

#try:
#    from gpiozero import LED
#except:
#    from fakegpiozero import LED

from valve_drv import ValveDrvThread
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

bmp085_i = BMP085(bus=1, address=0x77)
bmp085_e = BMP085(bus=4, address=0x77)

# this device should be address 0x48
def read_ai0():
    try:
        bus.write_byte(0x48, 0 & 0x03) # select the channel
        bus.write_byte(0x48, 0) # give it time to convert
        return bus.read_byte(0x48)
    except IOError as e:
        print('Read AI error! ', e)
        return 31

def read_all():

    #from time import sleep
    #sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info
    #from random import random


    #print('reading p_i')
    p_i, t_i = bmp085_i.read()
    #print('reading p_i')
    p_e, t_e = bmp085_e.read()
    # Scale factor, sf. 
    #sf = 5 # When sensor is on inspiratory line.
    sf = 10 # When sensor is on expiratory line.
    q_i = sf*(read_ai0() - 31) # 31 seems to be zero flow.
    #q_i = 0
    
    return {
        't': time.time(),
        'q_i': q_i,
        'q_e': None,
        'p_i': p_i, 
        'p_e': p_e,
        't_i': t_i,
        't_e': t_e,
        'o_i': None,
        'o_e': None,
    }


class SensorsThread(threading.Thread):
    def __init__(self, fs=10, daemon=True, maxnvalues=100, read_all_duration=0.11, **kwargs):
        threading.Thread.__init__(self)
        self.p_set_point = 0
        self.rl_p_set_point = RateLimiter(-50, 100, 1/30)
        self.rl_p = RateLimiter(-50, 100, 1/15)
        #self.rl_u = RateLimiter(-.25, .5, 1/15)
        self.rl_u = RateLimiter(-.1, .2, 1/15)
        #self.pidf = PIDF(0.4, 0, 0, 0.0)
        #self.pidf = PIDF(0.01, 0.008, 0, 0.00, iLimits=[0, .2], uLimits=[0, 10]) # ok
        self.pidf = PIDF(0.01, 0.01, 0.0, 0.002, iLimits=[0, .2], uLimits=[0, 10])
        # 2 Hz.
        #self.lpf_p = LPF([0.00355661, 0.00711322, 0.00355661], [ 1., -1.78994555,0.80417199])
        # 5 Hz at fs=15
        #[0.05628602, 0.16885807, 0.16885807, 0.05628602]
        self.lpf_p = LPF([ 0.02224617,  0.08898467,  0.13347701,  0.08898467,  0.02224617], [ 1.        , -1.18741255,  0.74859907, -0.23634219,  0.03109435])

        self.i_valve_id = 0
        self.e_valve_id = 2
        self.stopped = threading.Event()
        self.delay = timedelta(seconds=(max(0, 1./fs - read_all_duration)))
        print(self.delay)
        self.samples_recv = 0
        self.current_values = collections.deque(maxlen=maxnvalues)
        self.daemon = daemon # if set auto-terminate when main thread exits
        #self.valves = [LED(17), LED(18), LED(22)]
        self.inspiration = False # for tracking inspiration/expiration
        self.V = ValveDrvThread([17, 18, 22], fs=400)
        for k,v in kwargs.items():
            setattr(self, k, v) # e.g. installed_flow_meters
        self.start()
        

    def stop(self):
        self.stopped.set()
        self.join()

    #def send_to_valve(self, valve_id, signal):
    #    # Make some sort of PWM
    #    if signal > 0:
    #        self.valves[valve_id].on()
    #    else:
    #        self.valves[valve_id].off()
        
        
    def run(self):
        while not self.stopped.wait(self.delay.total_seconds()):
            current_val = read_all()
            if self.inspiration and len(self.current_values) > 0:
                if current_val['p_i'] < 0:
                    current_val['p_i'] = self.current_values[-1]['p_i']
                if current_val['p_e'] < 0:
                    current_val['p_e'] = self.current_values[-1]['p_e']
                    
            #current_val['ie'] = self.ie # not needed, but maybe helpful for debugging

            # integrate tidal volume
            if len(self.current_values)>1: # catch the case when no data yet acquired
                dt = current_val['t'] - self.current_values[-1]['t']
                dtv = (current_val['q_i'] + self.current_values[-1]['q_i'])/2 * dt
                if self.installed_flow_meters=='I':
                    if self.inspiration:
                        current_val['tv_i'] = self.current_values[-1]['tv_i'] + dtv
                    else:
                        current_val['tv_i'] = 0 # FIXME: patient exhales instantaneously!!!
                elif self.installed_flow_meters=='E':
                    if self.inspiration:
                        # start simple with just -ve 
                        current_val['tv_i'] = 0 # FIXME: patient INHALES instantaneously!!!
                    else:
                        current_val['tv_i'] = self.current_values[-1]['tv_i'] + dtv
                else:
                    raise ValueError('Unknown value for installed_flow_meters=%s % self.installed_flow_meters')
            else:
                current_val['tv_i'] = 0 # default value
            
            if self.inspiration or True:
                p_set_point_rl = self.rl_p_set_point.update(self.p_set_point)
            else:
                p_set_point_rl = self.p_set_point
            #p_set_point_rl = self.p_set_point
            #print(p_set_point_rl)
            y = self.rl_p.update(current_val['p_e'])
            y = self.lpf_p.update(y)
            current_val['y'] = y
            current_val['y_s'] = p_set_point_rl
            current_val['u'] = self.pidf.calc_output(y, p_set_point_rl)
            current_val['u_f'] = self.rl_u.update(current_val['u'])
            #print('%.3f' % current_val['u'])

            #print('%2.0f\t%2.0f\t%2.0f' % (self.p_set_point, self.current_values[-1]['p_i'] - 988, u))
            #print(' '*2*int(p_set_point_rl) + 's')
            #print(' '*2*int(self.current_values[-1]['p_i']) + 'p')
            #print(' '*int(u) + 'u')
            
            # Send control signals to valves.
            if self.inspiration:
                self.V.u[0] = current_val['u_f']
                self.V.u[2] = 0
            else:
                #self.V.u[0] = 0
                self.V.u[0] = current_val['u_f']
                self.V.u[2] = 1
                #if current_val['p_e'] > p_set_point_rl:
                #    self.V.u[2] = 1
                #else:
                #    self.V.u[2] = 0
            
            self.current_values.append(current_val)
            self.samples_recv += 1

            
if __name__=="__main__":
    #T = SensorsThread(fs=10, daemon=False)
    print(read_bmp085_i(0x77))
        
