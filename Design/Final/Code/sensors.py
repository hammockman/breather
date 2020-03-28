"""
Acquire sensor data.

Sensor nomenclature:

- type: flow (q), pressure (p), temp (t), humidity (h), O2 (o) 
- location: high pressure (isnpiration), low pressure (expiration)

jh, Mar 2020


Ra would like:

sensors = [
 {'name': 'Insp. pressure', 
'sensor_type': 'hmb085', 
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
try:
    import smbus
except:
    import fakesmbus as smbus
import collections
import time

# at the moment I'm hoping to simply grab everything once per control loop
# if it turns out sensors are slow/variable to read then this plan will change
__all__ = ["read_all", "Sensors"] 



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

def read_hmb085(address):

    import time

    bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) if you have a revision 2 board 

    def read_byte(offset):
        return bus.read_byte_data(address, offset)
    
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

    def write_byte(offset, value):
        bus.write_byte_data(address, offset, value)


    calibration = bus.read_i2c_block_data(address, 0xAA, 22)
    oss = 0
    test = False

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


    #print("Raw temp:", temp_raw)
    #print("Raw pressure:", pressure_raw)



    #Calculate temperature
    x1 = ((temp_raw - ac6) * ac5) / 32768
    x2 = (mc * 2048) / (x1 + md)
    b5 = x1 + x2
    t = (b5 + 8) / 16
    #print("Temp: ", t / 10.0, "degrees C")

    b6 = b5 - 4000 ; #print("b6 = ", b6)
    x1 = int(b2 * int(b6 * b6) >> 12) >> 11 ; #print("x1 = ",x1)
    x2 = int(ac2 * b6) >> 11 ; #print("b6x2 = ",x2)
    x3 = x1 + x2 ; #print("x3 = ",x3)
    b3 = int((int(ac1 * 4 + x3) << oss) + 2) >> 2 ; #print("b3 = ",b3)

    x1 = int(ac3 * b6) >> 13 ; #print("x1 = ",x1)
    x2 = int(b1 * int(int(b6 * b6) >> 12)) >> 16 ; #print("x2 = ",x2)
    x3 = int((x1 + x2) + 2) >> 2 ; #print("x3 = ",x3)
    b4 = int(ac4 * (x3 + 32768)) >> 15 ; #print("b4 = ",b4)
    b7 = (pressure_raw - b3) * (int(50000) >> oss) ; #print("b7 = ",b7)
    if (b7 < 0x80000000):
        p = (b7 * 2) /b4 ; #print("p = ",p)
    else:
        p = (b7 / b4) *2 ; #print("p1 = ",p)
    x1 = (int(p) >> 8) * (int(p) >> 8) ; #print("x1 = ",x1)
    x1 = int(x1 * 3038) >> 16 ; #print("x1 = ",x1)
    x2 = int(-7357 * p) >> 16 ; #print("x2 = ",x2)
    p = p + (int(x1 + x2 + 3791) >> 4) ; #print("pressure = ",p,"Pa")
    
    return p, t


def read_all():

    from time import sleep
    #sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info
    #from random import random


    p_h, t_h = read_hmb085(address=0x77)
    
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
    def __init__(self, fs=10, daemon=True, maxnvalues=100):
        threading.Thread.__init__(self)
        self.stopped = threading.Event()
        self.delay = timedelta(seconds=1./fs)
        self.samples_recv = 0
        self.current_values = collections.deque(maxlen=maxnvalues)
        self.daemon = daemon # if set auto-terminate when main thread exits
        self.start()

        
    def stop(self):
        self.stopped.set()
        self.join()

        
    def run(self):
        while not self.stopped.wait(self.delay.total_seconds()):
            self.current_values.append(read_all())
            self.samples_recv += 1
            #if self.samples_recv%30==0: print(self.current_values)

            
if __name__=="__main__":
    #T = SensorsThread(fs=10, daemon=False)
    print(read_hmb085(0x77))
        
