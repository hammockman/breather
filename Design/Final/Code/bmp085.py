import time
try:
    import smbus
except:
    import fakesmbus as smbus
from utils import get_word, twos_compliment
    
class BMP085():

    def __init__(self, address):
        self.address = address
        self.bus = smbus.SMBus(1) # or bus = smbus.SMBus(1) if you have a revision 2 board 

        # Move this stuff out to init.

        calibration = self.bus.read_i2c_block_data(address, 0xAA, 22)
        self.oss = 0
        test = False

        self.ac1 = get_word(calibration, 0, True)
        self.ac2 = get_word(calibration, 2, True)
        self.ac3 = get_word(calibration, 4, True)
        self.ac4 = get_word(calibration, 6, False)
        self.ac5 = get_word(calibration, 8, False)
        self.ac6 = get_word(calibration, 10, False)
        self.b1 =  get_word(calibration, 12, True)
        self.b2 =  get_word(calibration, 14, True)
        self.mb =  get_word(calibration, 16, True)
        self.mc =  get_word(calibration, 18, True)
        self.md =  get_word(calibration, 20, True)
    
    def read_byte(self, offset):
        return self.bus.read_byte_data(self.address, offset)
    
    def read_word(self, adr):
        high = self.bus.read_byte_data(self.address, adr)
        low = self.bus.read_byte_data(self.address, adr+1)
        val = (high << 8) + low
        return val

    def read_word_2c(self, adr):
        val = self.read_word(adr)
        if (val >= 0x8000):
            return -((0xffff - val) + 1)
        else:
            return val

    def write_byte(self, offset, value):
        self.bus.write_byte_data(self.address, offset, value)


    def read(self):
        # Seems like we have to wait between write and read. 0.003 s seems 
        # like a minimum. Can't make this sequential?
        # Read raw temperature
        self.write_byte(0xF4, 0x2E)
        time.sleep(0.003)
        temp_raw = self.read_word_2c(0xF6)

        self.write_byte(0xF4, 0x34 + (self.oss << 6))
        time.sleep(0.003)
        pressure_raw = ((self.read_byte(0xF6) << 16) + (self.read_byte(0xF7) << 8) + (self.read_byte(0xF8)) ) >> (8-self.oss)



        #print("Raw temp:", temp_raw)
        #print("Raw pressure:", pressure_raw)



        #Calculate temperature
        x1 = ((temp_raw - self.ac6) * self.ac5) / 32768
        x2 = (self.mc * 2048) / (x1 + self.md)
        b5 = x1 + x2
        t = (b5 + 8) / 160 # Print statement below used to have a /10
        #print("Temp: ", t, "degrees C")

        b6 = b5 - 4000 ; #print("b6 = ", b6)
        x1 = int(self.b2 * int(b6 * b6) >> 12) >> 11 ; #print("x1 = ",x1)
        x2 = int(self.ac2 * b6) >> 11 ; #print("b6x2 = ",x2)
        x3 = x1 + x2 ; #print("x3 = ",x3)
        b3 = int((int(self.ac1 * 4 + x3) << self.oss) + 2) >> 2 ; #print("b3 = ",b3)
    
        x1 = int(self.ac3 * b6) >> 13 ; #print("x1 = ",x1)
        x2 = int(self.b1 * int(int(b6 * b6) >> 12)) >> 16 ; #print("x2 = ",x2)
        x3 = int((x1 + x2) + 2) >> 2 ; #print("x3 = ",x3)
        b4 = int(self.ac4 * (x3 + 32768)) >> 15 ; #print("b4 = ",b4)
        b7 = (pressure_raw - b3) * (int(50000) >> self.oss) ; #print("b7 = ",b7)
        if (b7 < 0x80000000):
            p = (b7 * 2) /b4 ; #print("p = ",p)
        else:
            p = (b7 / b4) *2 ; #print("p1 = ",p)
        x1 = (int(p) >> 8) * (int(p) >> 8) ; #print("x1 = ",x1)
        x1 = int(x1 * 3038) >> 16 ; #print("x1 = ",x1)
        x2 = int(-7357 * p) >> 16 ; #print("x2 = ",x2)
        p = p + (int(x1 + x2 + 3791) >> 4) ; #print("pressure = ",p,"Pa")
        p = p/100 # hPa or cm H20
        
        return p, t
