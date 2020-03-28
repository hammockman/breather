"""
Misc bits'n'bobs.

jh, Mar 2020
"""


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
    
    
if __name__=="__main__":
    print(ibw2tv(height2ibw('m', 192)))
    print(ibw2tv(height2ibw('f', 192)))
