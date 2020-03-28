"""
Pretend to do whatever it is smbus does


jh, Mar 2020
"""

class SMBus():

    def __init__(self, n):
        pass

    def write_byte_data(self, address, offset, value):
        pass

    def read_byte_data(self, address, offset):
       return ( 162 ) 

    def read_i2c_block_data(self, address, offset, nbytes):
        return ( [34, 111, 251, 46, 200, 52, 131, 35, 98, 45, 72, 58, 25, 115, 0, 51, 128, 0, 209, 246, 10, 179] )
    
    
