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


dev_num = 0  # defines which ADS1220 is read. 2 means the program will alternatie between 0 and 1

flip_bit = 0

# device identification data
DEV_NAME = "Temperature Monitor"
DEV_VERSION = "1.0.1"
DEV_LOCATION = "Internal sensor"

# ADS1220 configuration data
# reg 0: AIN = AIN1 - AIN0, gain 8, PGA enabled
# reg 1: data rate 20 SPS, normal mode, cont mode, temp sensor off, burn-out sources off
# reg 2: ext ref REFP0 and REFN0, 50 Hz filter, power switch always open, 250 uA IDAC
# reg 3: IDAC1 connected to AIN3, IDAC2 disabled, dedicated DRDY pin only
ADS_REG0 = 0x66
ADS_REG1 = 0x04
ADS_REG2 = 0x64
ADS_REG3 = 0x80

# the reference resitor and the ADS1220 gain
RREF = 1000.0
GAIN = 8
LSB = 2 * RREF / GAIN / pow(2, 24)

# some timing values
F_CPU = int(100e6)
START_DELAY = 0.1
LOOP_PERIOD = 0.5

spi = spidev.SpiDev()      # Erstelle ein SPI-Objekt
spi.open(0, 0 )             # Öffne SPI-Bus 0, Device (CS) 0

spi1 = spidev.SpiDev()      # Erstelle ein SPI-Objekt
spi1.open(0, 1 ) 
# Konfiguration
spi.max_speed_hz = 50000   # Setze die maximale Geschwindigkeit auf 50 kHz
spi.mode = 0b01         # Setze den SPI-Modus auf 0

spi1.max_speed_hz = 50000   # Setze die maximale Geschwindigkeit auf 50 kHz
spi1.mode = 0b01


def spi_transceive(data):
    global flip_bit
    if dev_num == 0: 
        response = spi.xfer2(data)
        
    elif dev_num == 1:
        response = spi1.xfer2(data)
        
    elif dev_num == 2 and flip_bit == 0:
        response = spi.xfer2(data)
        flip_bit = 1
        
    elif dev_num == 2 and flip_bit == 1:
        response = spi1.xfer2(data)
        flip_bit = 0
    return response

def reset():
    spi_transceive([0x06])



def start_sync():
    spi_transceive([0x08])


def wreg(reg, value):
    spi_transceive([0x40 | ((0x03 & reg) << 2), value])
    if dev_num == 2:
        spi_transceive([0x40 | ((0x03 & reg) << 2), value])
        

def rdata():
    data = spi_transceive([0x10, 0, 0, 0])
    d_uint = (data[1] << 16) + (data[2] << 8) + data[3]
    return d_uint - int((d_uint << 1) & 2**24)


def pt100_r2t(R_T):
    R_0 = 100.0
    A = 3.9083e-3
    B = -5.775e-7
    return (-A + pow(A**2 - 4*B*(1-R_T/R_0), 0.5)) / 2 / B


# MicroPython doesn't support Unicode exceptions so we need this helper
# to check make sure only ASCII charaters are transfered
def isascii(s):
    return len(s) == len(s.encode())


reset()

wreg(0, ADS_REG0)
wreg(1, ADS_REG1)
wreg(2, ADS_REG2)
wreg(3, ADS_REG3)

start_sync()

time.sleep(START_DELAY)

# d = collections.OrderedDict()
# d["Device"] = collections.OrderedDict()
# d["Device"]["Name"] = DEV_NAME
# d["Device"]["Version"] = DEV_VERSION
# d["Device"]["Location"] = DEV_LOCATION
# d["Data"] = collections.OrderedDict()

while True:
    # if dev_num == 2:
    #     d["Device"]["Channel"] = flip_bit
    # else:
    #     d["Device"]["Channel"] = dev_num
    d_int = rdata()
    r_ohm = d_int * LSB
    t_degc = pt100_r2t(r_ohm)

    
    # d["Data"]["Binary"] = collections.OrderedDict({"Value": d_int})
    # d["Data"]["Resistance"] = collections.OrderedDict({"Value": r_ohm, "Unit": "Ohm"})
    # d["Data"]["Temperature"] = collections.OrderedDict({"Value": t_degc, "Unit": "degC"})
    # json_str = json.dumps(d)
    # if isascii(json_str):
    #     print(json_str)
    curr_temp = round(t_degc, 2)
    print(f'Temperature: {curr_temp}')
    time.sleep(LOOP_PERIOD)
