import RPi.GPIO as GPIO
from time import sleep, strftime
import time
from multiprocessing import Process, Pipe
import math
from datetime import datetime
import pidpy as PIDController
import csv
import bme280_76
import bme280_77

(chip_id, chip_version) = bme280_76.readBME280ID()
print ("Chip ID     :" + str(chip_id))
print ("Version     :" + str(chip_version))

(temperature, pressure, humidity) = bme280_76.readBME280All()
h = humidity
t = temperature
print("Sensor 76: ", h, t)


(chip_id, chip_version) = bme280_77.readBME280ID()
print ("Chip ID     :" + str(chip_id))
print ("Version     :" + str(chip_version))

(temperature, pressure, humidity) = bme280_77.readBME280All()
h = humidity
t = temperature
print("Sensor 77: ", h, t)