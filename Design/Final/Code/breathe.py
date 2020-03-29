"""
Ventillator contol program

Threads:

1. main: control loop + valve actuation 
2. sensor: reads sensor data, update
3. messaging: MQTT handling


Ventilator Modes:

AC (CMV) - assist control (continuous mandatory ventilation). Fixed volume. Patient triggered with time based override. Monitor pressure. Alarms: high peak pressure, high plateau pressure
PC - pressure control. Fixed pressure. Patient or time triggered. Monitor volume.
CPAP, PEEP - continuous pressure , positive end expiratory pressure
PS - pressure support. Specific pressure for each Inhalation only. Patient triggered.

8mg/kg ideal body weight

Qns:

* can gpio be accessed from multiple threads?

jh, Mar 2020
"""

from messaging import MessagingThread
from sensors import SensorsThread
from time import sleep
import json

subscribe_to_topics = {
    # topic: (default_value, on_message_callback_function_name)
    'breathe/runstate': ('run', 'runstate'), # run, pause, quit
    'breathe/runmode': ('AC', None), # AC=CMV, PC, ...
    'breathe/fio2': (0.5, None), # fraction inspired oxygen 
    'breathe/tv': (550, None), # ml; tidal volume
    'breathe/rate': (16, None), # min^-1; backup breathing rate
    'breathe/peep': (5, None), # mmH20; positive end expiratory pressure
    'breathe/ieratio': (1, None), # in:exp-iration ratio
    
}

M = MessagingThread(subscribe_to_topics)
S = SensorsThread(fs=50, maxnvalues=100, read_all_duration=.02) # (fs,ms/sample): (1, 1.1) (2, .61) (3, .44) (5, .31) (10, .2) (100, .12)

inspiration = True

p_i = 40
p_e = 10


def deque2dict(q):
    """
    render a collections.deque list-of-dicts as a dict-of-lists
    """
    out = {k:[] for k in q[0].keys()}
    for k in out.keys():
        for d in q:
            out[k].append(d[k])
    return out
        

nbreaths = 0
while True: # main control loop
    nbreaths += 1
    inspiration = not inspiration
    
    # todo: implement breathing 
    sleep(5)
    if inspiration:
        S.p_set_point = p_i
    else:
        S.p_set_point = p_e

    # publish sensor values
    M.publish('breathe/sensors/current', json.dumps(deque2dict(S.current_values)), retain=True)
    print(nbreaths, S.samples_recv, len(S.current_values))
    M.publish('breathe/nbreaths', nbreaths, retain=True)
        
    # exit if instructed to
    if M.messages['breathe/runstate'] == 'quit':
        # todo: write current state for restore on restart
        exit(0)
