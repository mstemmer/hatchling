from time import sleep
import RPi.GPIO as GPIO

stepPin = 31
sleepPin = 29
stepsPerRound = 200  # Step angle is 1.8°, so 200 steps to complete the 360° in full step mode

GPIO.setmode(GPIO.BOARD)
GPIO.setup(sleepPin, GPIO.OUT)
GPIO.setup(stepPin, GPIO.OUT)
# M0, M2 are pulled high with 3.3V to set Mode 101 --> 32 microsteps/step
# direction pin is not defined, need only one direction

step_count = stepsPerRound * 32
delay = .0208 / 32


def moveEggs() :
    
    GPIO.output(sleepPin, GPIO.HIGH)
    sleep(0.2) # wakeup time is min 1 millisecond

    for x in range(step_count):
        GPIO.output(stepPin, GPIO.HIGH)
        sleep(delay)
        GPIO.output(stepPin, GPIO.LOW)
        sleep(delay)
    
    sleep(4)

    #GPIO.output(sleepPin, GPIO.LOW) #DRV8825 into sleep mode --> draws much less energy
    

if __name__ == '__main__':
    moveEggs()
    GPIO.cleanup() 

