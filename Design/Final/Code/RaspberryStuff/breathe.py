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

subscribe_to_topics = {
    # topic: (default_value, on_message_callback_function_name)
    'breathe/runstate': ('run', 'runstate'), # run, pause, quit
    'breathe/runmode': ('AC', 'runmode'), # AC=CMV, PC, ...
    'breathe/fio2': (0.5, 'fio2'), # fraction inAC=CMV, PC, ...
    'breathe/tv': (550, 'tv'), # tidal volume
    'breathe/rate': (, 'rate'), # backup breathing rate
    'breathe/peep': (5, 'rate'), # mmH20 positive end expiratory pressure
}

M = MessagingThread(subscribe_to_topics)
S = SensorsThread()
nbreaths = 0
while True: # main control loop
    nbreaths += 1
    
    # todo: implement breathing 
    sleep(5)

    # publish sensor values etc
    for k, v in S.current_values.items():
        M.publish('breathe/sensors/'+k, v, retain=True)
    print(nbreaths)
    M.publish('breathe/nbreaths', nbreaths, retain=True)
        
    # exit if instructed to
    if M.messages['breathe/runstate'] == 'quit':
        # todo: write current state for restore on restart
        exit(0)
