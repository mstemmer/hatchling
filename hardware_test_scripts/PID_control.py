from hardware_test_scripts.temp_sense_class import TempSense
from simple_pid import PID
import RPi.GPIO as GPIO
import time
import math
import sys
import logging



class TempControl:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.heat_pin = 12
        self.dir_pin = 26

        pins = [self.heat_pin, self.dir_pin]

        for p in pins :
            GPIO.setup(p, GPIO.OUT)
        GPIO.output(self.heat_pin, GPIO.LOW)
        
        self.pid = PID(290, 70, 10) # init pid controller 290, 70, 10
        self.heat = GPIO.PWM(self.heat_pin, 100)
        self.heat.start(0)
        
        self.pid.output_limits = (0, 100)
        self.pid.sample_time = None
        # self.pid.tunings = (config["PID_parameters"]) # update PID controller with config parameters
        # self.pid.proportional_on_measurement = True

        self.temperature_0 = TempSense(0)
        self.temperature_1 = TempSense(1)

    def set_direction(self, set_temp):
        if set_temp > 20:
            self.pid.tunings = (290, 70, 10) # change PID values
            self.pid.setpoint = set_temp
            GPIO.output(self.dir_pin, GPIO.HIGH)
        else:
            self.pid.tunings = (-290, -70, -10) # change PID values
            self.pid.setpoint = set_temp
            GPIO.output(self.dir_pin, GPIO.LOW)

    def control_temp(self, set_temp):
        
        self.set_direction(set_temp)
        print(self.temperature_1.get_temp())
        duty_cycle = self.pid(self.temperature_1.get_temp())
        print(duty_cycle)
        # duty_cycle = 20
        self.heat.ChangeDutyCycle(duty_cycle)
        print(duty_cycle)
        time.sleep(0.2)

    def shutdown(self):
        self.heat.ChangeDutyCycle(0)
        GPIO.output(self.heat_pin, GPIO.LOW)
        print("Duty cycle stopped)")







if __name__ == '__main__':

#     temperature_0 = TempSense(0)
#     temperature_1 = TempSense(1)
    try:
        pid = TempControl()
        while True:
            pid.control_temp(10)
    
#     # print(temperature_0.get_temp())
#     # print(temperature_1.get_temp())

#     while True:
#         print(temperature_0.get_temp())
#         pid.
#         time.sleep(0.3)
    
    
    
    # try:
    #     None



    except KeyboardInterrupt:
        pid.shutdown()