from time import sleep
from RPi import GPIO

fanPin = 18

GPIO.setmode(GPIO.BCM)
GPIO.setup(fanPin, GPIO.OUT)
GPIO.output(fanPin, GPIO.LOW)


fan = GPIO.PWM(fanPin, 25)
fan.start(0)


# fan.ChangeDutyCycle(50)
sleep(6)

