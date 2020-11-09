import pigpio
from time import sleep
# this connects to the pigpio daemon which must be started first
pi = pigpio.pi()
# Pigpio DHT22 module should be in same folder as your program
import DHT22

for i in range(1,20) :
    s = DHT22.sensor(pi, 4)
    s.trigger()
    sleep(3) # Necessary on faster Raspberry Pi's
    print('Temp={:3.2f}  Humidity={:3.2f}%'.format((s.temperature() / 1.), s.humidity() / 1.))

    #print('Humidity={:3.2f}'.format(s.temperature() / 1.))

    #print ('DHT22 #1 Temp={0:0.1f}°C  Humidity={1:0.1f}%'.format(t, h))
s.cancel()
pi.stop()
