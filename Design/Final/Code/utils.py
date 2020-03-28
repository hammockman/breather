"""
Misc bits'n'bobs.

jh, Mar 2020
"""


def height2ibw(gender, height_cm):
    if gender=='f':
        return 45.5 + 2.3*(height_cm - 5*12*2.54)/2.54
    elif gender=='m':
        return 50.0 + 2.3*(height_cm - 5*12*2.54)/2.54



if __name__=="__main__":
    print(height2ibw('m', 192))
