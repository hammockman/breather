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
from time import time, sleep
import json

def deque2dict(q):
    """
    render a collections.deque list-of-dicts as a dict-of-lists
    """
    if len(q)==0: return {}
    out = {k:[] for k in q[0].keys()}
    for k in out.keys():
        for d in list(q):
            out[k].append(d[k])
    return out

# this is a list of messages that need to be READ
# no need to include message that will be written
subscribe_to_topics = {
    # topic: (default_value, on_message_callback_function_name)
    'breathe/runstate': ('run', 'runstate'), # run, pause, quit
    #'breathe/runmode': ('AC', None), # AC=CMV, PC, ...
    #'breathe/inputs/fio2': (0.5, None), # fraction inspired oxygen 
    #'breathe/inputs/tv': (550, None), # ml; tidal volume
    'breathe/inputs/bpm': (8, None), # min^-1; backup breathing rate
    'breathe/inputs/inp': (20, None), # cmH20; inspiration pressure
    'breathe/inputs/peep': (2, None), # cmH20; positive end expiratory pressure
    'breathe/inputs/ieratio': (1, None), # ins:exp-iration ratio
    'breathe/inputs/patrigmode': (1, None), # can the patient trigger inspiration?
}

M = MessagingThread(subscribe_to_topics)
print(M.messages)
fs = 30 # JH had 30
maxnvalues = int(180*fs/5) # 5 bpm is as low as it'll ever go???
S = SensorsThread(fs=fs, maxnvalues=maxnvalues, read_all_duration=.02)
# (fs,ms/sample): (1, 1.1) (2, .61) (3, .44) (5, .31) (10, .2) (100, .12)


flow_eps = 0. # the largest flow rate that should be considered "no flow"

def update_input(i):
    pth = 'breathe/inputs/'+i
    if pth in M.messages and M.messages[pth] is not None:
        print(i, pth, M.messages[pth])
        return M.messages[pth]
    else:
        return subscribe_to_topics[pth][0]


nbreaths = 0
t0 = time() # t0 tracks the start of inspiration
inspiration = True
S.p_set_point = update_input('inp')
M.publish('breathe/runstate','run'); sleep(2)
while True: # main control loop
    if M.messages['breathe/runstate'] == 'pause': continue
    
    # update control params based on current settings
    bpm = float(update_input('bpm'))
    #p_i = update_input('inp')
    #p_e = update_input('peep')
    ieratio = float(update_input('ieratio'))
    patrigmode = update_input('patrigmode')

    # deal with accumulated sensor data
    sensor_current_values = deque2dict(S.current_values)
    M.publish('breathe/sensors/current', json.dumps(sensor_current_values), retain=True)
    M.publish('breathe/nbreaths', nbreaths, retain=True)
    M.publish('breathe/bpm', bpm, retain=True) # eventually this will become the TRUE instantaneous breath rate c.f. backup bpm
    
    # exit if instructed to
    if M.messages['breathe/runstate'] == 'quit':
        # todo: write current state for restore on restart
        exit(0)
    # have we reached the end of the inspiration phase?
    # todo: get current flow rate
    t = time()
    if inspiration:
        flow = 100. # sensor_current_values['q_h']
        if flow<flow_eps or t>t0 + 60/bpm/(1. + ieratio):
            # force change over from ins- to ex-piration
            inspiration = False
            S.p_set_point = update_input('peep')
    else: # we're in expiration phase
        # trigger a new breath?
        exp_pressure = sensor_current_values['p_h'][-1] # p_l doesn't exist
        if (patrigmode and exp_pressure<0) or t>60/bpm:
            nbreaths += 1
            t0 = t
            inspiration = True
            S.p_set_point = update_input('inp')
            continue

    #print(nbreaths, ieratio)
    
    # go to sleep for a bit
    sleep(60/bpm/2) # was /5
        

