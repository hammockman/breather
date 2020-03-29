import numpy as np

class LPF():
  def __init__(self, b, a):
    self.b = b
    self.a = a
    self.x = np.zeros(len(b))
    self.y = np.zeros(len(a))
    
  def update(self, xNew):
    """ Rotate the input and output sequences 1 position to the right, add latest input
    value to zeroth position of x, update latest output value using ratio of inner products.
    """
    self.x[1:] = self.x[:-1]
    self.y[1:] = self.y[:-1]

    self.x[0] = xNew;
    #print(x.shape, y.shape, b.shape, a.shape)
    # Update y,
    self.y[0] = ((self.b*self.x).sum() - (self.a[1:]*self.y[1:]).sum())/self.a[0];
    return self.y[0];
