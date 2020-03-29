"""
Misc bits'n'bobs.

jh, Mar 2020
"""


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

def height2ibw(gender, height_cm):
    """Compute Ideal Body Weight from patient height.

    https://globalrph.com/medcalcs/adjusted-body-weight-ajbw-and-ideal-body-weight-ibw-calc/
    """
    if gender=='f':
        return 45.5 + 2.3*(height_cm - 5*12*2.54)/2.54
    elif gender=='m':
        return 50.0 + 2.3*(height_cm - 5*12*2.54)/2.54


def ibw2tv(ibw):
    """Tidal Volume from Ideal Body Weight
    """
    return 8*ibw # ml
    
class fakeLED():
    """
    Pretend to do whatever gpiozero.LED does.
    """
    def __init__(self, *args):
        pass

    def on(self):
        pass

    def off(self):
        pass


if __name__=="__main__":
    print(ibw2tv(height2ibw('m', 192)))
    print(ibw2tv(height2ibw('f', 192)))
