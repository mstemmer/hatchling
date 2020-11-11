import RPi.GPIO as GPIO
from multiprocessing import Process, Queue
import Adafruit_DHT
import pidpy as PIDController
import string
import time
import math
import sys

class BroodController():
    """ Reads data from two DHT22 sensors in a while loop. Reading alternates
    between the two sensors. Data is averaged over both, rounded and sent
    out via Queue(). Read values are checked for being numbers and loop is
    protected against read failures ocurring with DHT22 from time to time.
    This function also sets the status LEDs and regulates the heater
    automatically using a PID controller. The set_values are constantly
    evaluated."""

    def __init__(self, config, q_prog, q_data):
        GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by physical location
        GPIO.setwarnings(False)

        self.sensor_1 = config['setup_pin']['sensor_1']
        self.sensor_2 = config['setup_pin']['sensor_2']
        self.sensor = Adafruit_DHT.DHT22

        self.data_pin = config['setup_pin']['data']
        self.latch_pin = config['setup_pin']['latch']
        self.clock_pin = config['setup_pin']['clock']
        self.step_pin = config['setup_pin']['step']
        self.sleep_pin = config['setup_pin']['sleep']
        self.heat_pin = config['setup_pin']['heat']
        self.config = config

        pins = [self.data_pin, self.latch_pin, self.clock_pin,
        self.step_pin, self.sleep_pin, self.heat_pin]

        for p in pins :
            GPIO.setup(p, GPIO.OUT)
        GPIO.output(self.heat_pin, GPIO.LOW)

        self.heat = GPIO.PWM(self.heat_pin, 200)
        self.heat.start(0)

        # init class
        self.set_humid, self.set_temp = [55, 37]
        self.q_data = q_data
        self.q_prog = q_prog
        self.control()

    def read_program(self): #read incubation program sent by BroodLord
        if self.q_prog.empty() != True:
            self.set_humid, self.set_temp = self.q_prog.get()
        else:
            pass

        self.oor_temp_high = []
        self.oor_temp_low = []
        self.oor_humid_high = []
        self.oor_humid_low = []

        for val in range(4):
            temp_high = self.set_temp + self.config['LED_status']['oor_temp'][val]
            temp_low = self.set_temp - self.config['LED_status']['oor_temp'][val]
            humid_high = self.set_humid + self.config['LED_status']['oor_humid'][val]
            humid_low = self.set_humid - self.config['LED_status']['oor_humid'][val]
            self.oor_temp_high.append(temp_high)
            self.oor_temp_low.append(temp_low)
            self.oor_humid_high.append(humid_high)
            self.oor_humid_low.append(humid_low)

    def heater(self):
        # duty_cycle = pid.calcPID_reg4(self.temp, self.set_temp, True)
        self.duty_cycle = 0
        self.heat.ChangeDutyCycle(self.duty_cycle)

    def control(self):
        try:
            h_last, t_last = 30, 15 # need some start values
            i = 0
            while True:
                self.read_program()
                i+=1
                if i%2 == 0 : # test if dividable by 2, switch sensors for each cycle
                    sens = self.sensor_1
                else:
                    sens = self.sensor_2

                    try:
                        h, t = Adafruit_DHT.read_retry(self.sensor, sens)
                        # print('RAW', sens,h,t)
                        if math.isnan(h) == False and math.isnan(t) == False:
                            self.humid = round((h + h_last) / 2, 2) # make avg and round
                            self.temp = round((t + t_last) / 2, 2)
                            h_last, t_last = h, t # save current values for next sensor read
                            self.status_out()
                            self.heater()
                            self.q_data.put([self.humid, self.temp,
                            self.set_humid, self.set_temp, self.duty_cycle])
                            # print('AVG values read', self.humid, self.temp)
                            # print('Set values:', self.set_temp, self.set_humid)
                            time.sleep(1)

                        else :
                            print('Read value is NaN! Trying again...')
                            sleep(2)

                    except TypeError as e:
                        print("Reading from DHT22 failure: ",e.args)
                        time.sleep(2)

        except KeyboardInterrupt:
            self.heat.ChangeDutyCycle(0)
            GPIO.output(self.heat_pin, GPIO.LOW)
            print('Shutdown heater')
            sys.exit('Close program')

    def status_read(self) :
        if self.oor_temp_low[0] <= self.temp <= self.oor_temp_high[0] and \
            self.oor_humid_low[0] <= self.humid <= self.oor_humid_high[0]:
            self.status = self.config['mode'][1]
            return self.status

        elif self.oor_temp_low[1] <= self.temp <= self.oor_temp_high[1] and \
            self.oor_humid_low[0] <= self.humid <= self.oor_humid_high[0]:
            self.status = self.config['mode'][2]
            return self.status

        elif self.oor_temp_low[2] <= self.temp <= self.oor_temp_high[2] and \
            self.oor_humid_low[0] <= self.humid <= self.oor_humid_high[0]:
            self.status = self.config['mode'][3]
            return self.status

        elif self.oor_temp_low[3] <= self.temp <= self.oor_temp_high[3] and \
            self.oor_humid_low[0] <= self.humid <= self.oor_humid_high[0]:
            self.status = self.config['mode'][4]
            return self.status

        elif self.oor_temp_low[0] <= self.temp <= self.oor_temp_high[0] and \
            self.oor_humid_low[1] <= self.humid <= self.oor_humid_high[1]:
            self.status = self.config['mode'][5]
            return self.status

        elif self.oor_temp_low[1] <= self.temp <= self.oor_temp_high[1] and \
            self.oor_humid_low[1] <= self.humid <= self.oor_humid_high[1]:
            self.status = self.config['mode'][6]
            return self.status

        elif self.oor_temp_low[2] <= self.temp <= self.oor_temp_high[2] and \
            self.oor_humid_low[1] <= self.humid <= self.oor_humid_high[1]:
            self.status = self.config['mode'][7]
            return self.status

        elif self.oor_temp_low[3] <= self.temp <= self.oor_temp_high[3] and \
            self.oor_humid_low[1] <= self.humid <= self.oor_humid_high[1]:
            self.status = self.config['mode'][8]
            return self.status

        elif self.oor_temp_low[0] <= self.temp <= self.oor_temp_high[0] and \
            self.oor_humid_low[2] <= self.humid <= self.oor_humid_high[2]:
            self.status = self.config['mode'][9]
            return self.status

        elif self.oor_temp_low[1] <= self.temp <= self.oor_temp_high[1] and \
            self.oor_humid_low[2] <= self.humid <= self.oor_humid_high[2]:
            self.status = self.config['mode'][10]
            return self.status

        elif self.oor_temp_low[2] <= self.temp <= self.oor_temp_high[2] and \
            self.oor_humid_low[2] <= self.humid <= self.oor_humid_high[2]:
            self.status = self.config['mode'][11]
            return self.status

        elif self.oor_temp_low[3] <= self.temp <= self.oor_temp_high[3] and \
            self.oor_humid_low[2] <= self.humid <= self.oor_humid_high[2]:
            self.status = self.config['mode'][12]
            return self.status

        elif self.oor_temp_low[0] <= self.temp <= self.oor_temp_high[0] and \
            self.oor_humid_low[3] <= self.humid <= self.oor_humid_high[3]:
            self.status = self.config['mode'][13]
            return self.status

        elif self.oor_temp_low[1] <= self.temp <= self.oor_temp_high[1] and \
            self.oor_humid_low[3] <= self.humid <= self.oor_humid_high[3]:
            self.status = self.config['mode'][14]
            return self.status

        elif self.oor_temp_low[2] <= self.temp <= self.oor_temp_high[2] and \
            self.oor_humid_low[3] <= self.humid <= self.oor_humid_high[3]:
            self.status = self.config['mode'][15]
            return self.status

        else :
            self.status = self.config['mode'][16]
            return self.status

    def shift_out(self): #shift_out function, use bit serial transmission
        self.val = self.status_read()
        for i in range(0,8):
            GPIO.output(self.clock_pin,GPIO.LOW)
            GPIO.output(self.data_pin,(0x01&(self.val>>i)==0x01) and GPIO.HIGH or GPIO.LOW)
            GPIO.output(self.clock_pin,GPIO.HIGH)

    def status_out(self): #74HC595 will update the data to the parallel output port.
        GPIO.output(self.latch_pin,GPIO.LOW)  #Output low level to latchPin
        self.shift_out() #Send serial data to 74HC595
        GPIO.output(self.latch_pin,GPIO.HIGH) #Output high level to latchPin
        time.sleep(0.1)
