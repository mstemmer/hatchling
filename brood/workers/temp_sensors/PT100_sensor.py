# main.py
# MPIBI/JT
# 20220414

# MAKE SURE TO SET DEV_LOCATION AND USE_INTERNAL_SENSOR ACCORDINGLY

""" 
Temperature monitor script for use with ADS1220 Shield 1.0 PCB with PT100. The PT100 is measured 
using 4-wire configuration with a 1 kOhm resistor as reference. Two sensors can be read at the same time.
This code was written by Jürgen Tritthardt & Stefan Apel originally for use with RPI Pico. 
It was then adapted to work with the Raspberry Pi 3b.
"""

import collections
import json
import time
import spidev
import logging


class PT100TempSense:
    def __init__(self, dev_num):

        self.dev_num = dev_num  # defines which ADS1220 is read. 2 means the program will alternatie between 0 and 1
        self.flip_bit = 0

        # ADS1220 configuration data
        self.ADS_REG0 = 0x66 # reg 0: AIN = AIN1 - AIN0, gain 8, PGA enabled
        self.ADS_REG1 = 0x04 # reg 1: data rate 20 SPS, normal mode, cont mode, temp sensor off, burn-out sources of
        self.ADS_REG2 = 0x64 # reg 2: ext ref REFP0 and REFN0, 50 Hz filter, power switch always open, 250 uA IDAC
        self.ADS_REG3 = 0x80 # reg 3: IDAC1 connected to AIN3, IDAC2 disabled, dedicated DRDY pin on

        # the reference resitor and the ADS1220 gain
        RREF = 1000.0
        GAIN = 8
        self.LSB = 2 * RREF / GAIN / pow(2, 24)

        # some timing values
        self.F_CPU = int(100e6)
        self.START_DELAY = 0.1
        self.LOOP_PERIOD = 0.5

        self.spi = spidev.SpiDev()      # Erstelle ein SPI-Objekt
        self.spi.open(0, 0 )             # Öffne SPI-Bus 0, Device (CS) 0

        self.spi1 = spidev.SpiDev()     
        self.spi1.open(0, 1 ) 
        # Konfiguration
        self.spi.max_speed_hz = 50000   # Setze die maximale Geschwindigkeit auf 50 kHz
        self.spi.mode = 0b01         # Setze den SPI-Modus auf 0

        self.spi1.max_speed_hz = 50000   
        self.spi1.mode = 0b01

        self.reset()
        self.start_sync()



    def spi_transceive(self, data):
        if self.dev_num == 0: 
            response = self.spi.xfer2(data)
            
        elif self.dev_num == 1:
            response = self.spi1.xfer2(data)
        return response
    
    def wreg(self, reg, value):
        self.spi_transceive([0x40 | ((0x03 & reg) << 2), value])


    def reset(self):
        self.spi_transceive([0x06])
        self.wreg(0, self.ADS_REG0)
        self.wreg(1, self.ADS_REG1)
        self.wreg(2, self.ADS_REG2)
        self.wreg(3, self.ADS_REG3)


    def start_sync(self):
        self.spi_transceive([0x08])
        time.sleep(self.START_DELAY)
            

    def rdata(self):
        data = self.spi_transceive([0x10, 0, 0, 0])
        d_uint = (data[1] << 16) + (data[2] << 8) + data[3]
        return d_uint - int((d_uint << 1) & 2**24)


    def pt100_r2t(self, R_T):
        R_0 = 100.0
        A = 3.9083e-3
        B = -5.775e-7
        return (-A + pow(A**2 - 4*B*(1-R_T/R_0), 0.5)) / 2 / B
    
    def convert_temp(self):
        d_int = self.rdata()
        r_ohm = d_int * self.LSB
        t_degc = self.pt100_r2t(r_ohm)
        return t_degc
    
    def get_temp(self):
        temp = self.convert_temp()
        return temp
        



    # """  MicroPython doesn't support Unicode exceptions so we need this helper
    #     to check make sure only ASCII charaters are transfered """
    # def isascii(self, s):
    #     return len(s) == len(s.encode())

    
# if __name__ == '__main__':
#     temperature_0 = TempSense(0)
#     temperature_1 = TempSense(1)
    
#     # print(temperature_0.get_temp())
#     # print(temperature_1.get_temp())

#     while True:
#         print(temperature_1.get_temp())
#         time.sleep(0.3)
