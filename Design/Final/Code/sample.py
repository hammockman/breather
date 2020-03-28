
class (Sample):

  value = 0
  last_value = 0
  
  def __init__(self, name, units, alarm_low=None, alarm_high=None, read_fn=None):
    self.name = name
    self.units = units
    self.alarm_low = alarm_low
    self.alarm_high = alarm_high
    self.read = read_fn

  def to_mqtt():
    return {'name': self.name, 'value': self.value, 'units': self.units}


  
