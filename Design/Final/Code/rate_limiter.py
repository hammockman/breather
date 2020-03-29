import numpy as np

class RateLimiter():
  """
   Rate limiter. Returns a rate limited version of a signal. The rate
  limit can depend on direction (think of a VU meter with different rise
  and fall times). The signal should not have a lot of energy above the
  the reciprocal of the fastest limit (client is responsible at this
  stage!).

Units er units/seconds.

"""
  def __init__(self, lowerLimit, upperLimit, dt):
    self.limits = np.array([-np.inf, np.inf])
    self.limits[0] = lowerLimit;
    self.limits[1] = upperLimit;
    self.dt = dt;
    self.y = self.yPrev = 0.;


  def update(self, yRaw):
    if ((yRaw - self.y) / self.dt > self.limits[1]):
      y = self.y + self.limits[1] * self.dt;
    elif ((yRaw - self.y) / self.dt < self.limits[0]):
      self.y = self.y + self.limits[0] * self.dt
    else:
      self.y = yRaw
      
    return self.y;
