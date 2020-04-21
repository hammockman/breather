"""

"""
import numpy as np
import threading
from datetime import timedelta
import time

try:
    from gpiozero import LED
except:
    from fakegpiozero import LED


__all__ = ["ValveDrvThread"] 


class ValveDrvThread(threading.Thread):
    def __init__(self, valveGPIOs, fs=50, cycleTime=0.05, daemon=True):
        """fs is how many updates to the PWM every second. cycleTime is the total time of the PWM cycle.


        """
        threading.Thread.__init__(self)
        self.daemon = daemon # if set auto-terminate when main thread exits
        self.valveGPIOs = valveGPIOs
        self.valves = [LED(id) for id in valveGPIOs]
        self.M = len(self.valveGPIOs)

        # Control signal (updated by caller). Used range is 0-1.
        self.u = np.zeros(self.M)
        self.uInForce = np.zeros(self.M)
        self.updateUEveryN = 1
        self.n = 0 # How far through the duty time we are.
        self.N = int(cycleTime*fs)

        self.delay = timedelta(seconds=(max(0, 1./fs)))
        self.stopped = threading.Event()
        
        self.start()
        

    def stop(self):
        self.stopped.set()
        self.join()

    def run(self):
        while not self.stopped.wait(self.delay.total_seconds()):
            # Only update the u every updateUEveryN time increments.
            if self.n % self.updateUEveryN == 0:
                self.uInForce = self.u
                #print('%.5f\t\t\t%d' % (self.uInForce[0], self.n))

            # For every valve then update the GPIO pin.
            for i in range(self.M):
                if self.n < self.N*self.uInForce[i]:
                    #if i == 0: print('     -', self.N, self.uInForce[0])
                    self.valves[i].on()
                else:
                    #if i == 0: print('-     ', self.N, self.uInForce[0])
                    self.valves[i].off()

            # Update n.
            self.n = self.n+1
            if self.n >= self.N:
                self.n = 0

            
if __name__=="__main__":
    pass
