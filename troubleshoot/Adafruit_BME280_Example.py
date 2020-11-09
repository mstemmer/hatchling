from Adafruit_BME280_76 import *
from Adafruit_BME280_77 import *
import Adafruit_GPIO
import Adafruit_PureIO


sensor_1 = BME280_76(t_mode=BME280_76_OSAMPLE_8, p_mode=BME280_76_OSAMPLE_8, h_mode=BME280_76_OSAMPLE_8)

degrees = sensor_1.read_temperature()
pascals = sensor_1.read_pressure()
hectopascals = pascals / 100
humidity = sensor_1.read_humidity()

print ('Temp      = {0:0.3f} deg C'.format(degrees))
print ('Pressure  = {0:0.2f} hPa'.format(hectopascals))
print ('Humidity  = {0:0.2f} %'.format(humidity))

sensor_2 = BME280_77(t_mode=BME280_77_OSAMPLE_8, p_mode=BME280_77_OSAMPLE_8, h_mode=BME280_77_OSAMPLE_8)

degrees = sensor_2.read_temperature()
pascals = sensor_2.read_pressure()
hectopascals = pascals / 100
humidity = sensor_2.read_humidity()

print ('Temp      = {0:0.3f} deg C'.format(degrees))
print ('Pressure  = {0:0.2f} hPa'.format(hectopascals))
print ('Humidity  = {0:0.2f} %'.format(humidity))