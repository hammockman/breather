"""
Acquire sensor data.

Sensor nomenclature:

- type: flow (q), pressure (p), temp (t), humidity (h), O2 (o) 
- location: high pressure (isnpiration), low pressure (expiration)

jh, Mar 2020
"""

# at the moment I'm hoping to simply grab everything once per control loop
# if it turns out sensors are slow/variable to read then this plan will change
__all__ = ["read_all"] 

def read_all():

    from time import sleep
    sleep(0.05) # hopefully 50ms is an over-estimate of the time it'll take to readout all the sensor info

    return {
        'q_h':None,
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
