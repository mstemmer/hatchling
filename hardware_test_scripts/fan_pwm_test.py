from time import sleep
from RPi import GPIO
from rpi_hardware_pwm import HardwarePWM

fanPin = 19

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(fanPin, GPIO.OUT)
# GPIO.output(fanPin, GPIO.LOW)


# fan = GPIO.PWM(fanPin, 15000)
# fan.start(0)


# fan.ChangeDutyCycle(25)
# sleep(6)


pwm = HardwarePWM(pwm_channel=2, hz=25000, chip=2)
pwm.start(100) # full duty cycle

pwm.change_duty_cycle(70)
sleep(9)
# pwm.change_frequency(25_000)

pwm.stop()