import numpy as np

class PIDF():
    ''' Proportional Integral Derivative Feed-forward (PIDF)
    controller. The controller has limits on the integral component, and
    can also limit the maximum output value.
    '''
    def __init__(self, p=0., i=0., d=0., f=0., \
                     iLimits=np.array([-np.inf, np.inf]), \
                     maxOutput=np.inf):
        ''' Initialise by setting none, some or all of the PIDF
        parameters. The integrator limits and mximum output can also be
        set here.
        '''
        self.kP = p
        self.kI = i
        self.kD = d
        self.kF = f

        self.p = np.nan
        self.i = 0.
        self.d = 0.
        self.f = 0.
        
        self.y = 0.
        self.dt = 1.
        self.e = 0.
        self.u = 0.
        
        self.iMin = iLimits[0]
        self.iMax = iLimits[1]
        self.maxOutput = maxOutput
        
    def __str__(self):
        ''' Print a string of the current settings.
        '''
        return 'PIDF controller: k_p={}, k_i={}, k_d={}, k_f={})' \
            .format(self.kP, self.kI, self.kD, self.kF)

    def calc_output(self, y, setPoint):
        ''' *y* is the reading, *setPoint* is the desired value. The output of
        the PIDF controller is returned, and the error (*setPoint* - *y*) is
        recorded.
        '''
        e = setPoint - y
        self.p = self.kP*e
        self.i += self.kI*e*self.dt
        if self.i < self.iMin:
            self.i = self.iMin
        if self.i > self.iMax:
            self.i = self.iMax
        self.d = self.kD*(e-self.e)/self.dt
        if self.kF != 0 and not np.isnan(setPoint):
            self.f = self.kF*setPoint
        else:
            self.f = 0.
        #     Make selectable recording.

        self.e = e
        
        self.u = self.p + self.i + self.d + self.f
        #print self.p, self.i, self.d, self.f, output
        if self.u > self.maxOutput:
            return self.maxOutput
        else:
            return self.u
          
