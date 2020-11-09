import RPi.GPIO as GPIO
import Adafruit_DHT
import string
import time
import math

class BroodController():

    def __init__(self, config):
        GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by physical location
        GPIO.setwarnings(False)

        self.sensor_1 = config['setup_pin']['sensor_1']
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

        self.set_temp = 37 # to config! create json files for species
        self.set_humid = 55 # to config!

        self.oor_temp_a = config['LED_status']['oor_temp'][0]
        self.oor_temp_b = config['LED_status']['oor_temp'][1]
        self.oor_temp_c = config['LED_status']['oor_temp'][2]
        self.oor_temp_d = config['LED_status']['oor_temp'][3]

        self.oor_humid_a = config['LED_status']['oor_humid'][0]
        self.oor_humid_b = config['LED_status']['oor_humid'][1]
        self.oor_humid_c = config['LED_status']['oor_humid'][2]
        self.oor_humid_d = config['LED_status']['oor_humid'][3]

        self.sense_th()

    def status_read(self) :
        if self.temp >= self.set_temp - self.oor_temp_a and self.temp <= self.set_temp + self.oor_temp_a and \
            self.humid >= self.set_humid - self.oor_humid_a and self.humid <= self.set_humid + self.oor_humid_a:
            self.status = self.config['mode'][1]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_b and self.temp <= self.set_temp + self.oor_temp_b and \
            self.humid >= self.set_humid - self.oor_humid_a and self.humid <= self.set_humid + self.oor_humid_a:
            self.status = self.config['mode'][2]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_c and self.temp <= self.set_temp + self.oor_temp_c and \
            self.humid >= self.set_humid - self.oor_humid_a and self.humid <= self.set_humid + self.oor_humid_a:
            self.status = self.config['mode'][3]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_d and self.temp <= self.set_temp + self.oor_temp_d and \
            self.humid >= self.set_humid - self.oor_humid_a and self.humid <= self.set_humid + self.oor_humid_a:
            self.status = self.config['mode'][4]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_a and self.temp <= self.set_temp + self.oor_temp_a and \
            self.humid >= self.set_humid - self.oor_humid_b and self.humid <= self.set_humid + self.oor_humid_b:
            self.status = self.config['mode'][5]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_b and self.temp <= self.set_temp + self.oor_temp_b and \
            self.humid >= self.set_humid - self.oor_humid_b and self.humid <= self.set_humid + self.oor_humid_b:
            self.status = self.config['mode'][6]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_c and self.temp <= self.set_temp + self.oor_temp_c and \
            self.humid >= self.set_humid - self.oor_humid_b and self.humid <= self.set_humid + self.oor_humid_b:
            self.status = self.config['mode'][7]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_d and self.temp <= self.set_temp + self.oor_temp_d and \
            self.humid >= self.set_humid - self.oor_humid_b and self.humid <= self.set_humid + self.oor_humid_b:
            self.status = self.config['mode'][8]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_a and self.temp <= self.set_temp + self.oor_temp_a and \
            self.humid >= self.set_humid - self.oor_humid_c and self.humid <= self.set_humid + self.oor_humid_c:
            self.status = self.config['mode'][9]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_b and self.temp <= self.set_temp + self.oor_temp_b and \
            self.humid >= self.set_humid - self.oor_humid_c and self.humid <= self.set_humid + self.oor_humid_c:
            self.status = self.config['mode'][10]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_c and self.temp <= self.set_temp + self.oor_temp_c and \
            self.humid >= self.set_humid - self.oor_humid_c and self.humid <= self.set_humid + self.oor_humid_c:
            self.status = self.config['mode'][11]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_d and self.temp <= self.set_temp + self.oor_temp_d and \
            self.humid >= self.set_humid - self.oor_humid_c and self.humid <= self.set_humid + self.oor_humid_c:
            self.status = self.config['mode'][12]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_a and self.temp <= self.set_temp + self.oor_temp_a and \
            self.humid >= self.set_humid - self.oor_humid_d and self.humid <= self.set_humid + self.oor_humid_d:
            self.status = self.config['mode'][13]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_b and self.temp <= self.set_temp + self.oor_temp_b and \
            self.humid >= self.set_humid - self.oor_humid_d and self.humid <= self.set_humid + self.oor_humid_d:
            self.status = self.config['mode'][14]
            return self.status
        elif self.temp >= self.set_temp - self.oor_temp_c and self.temp <= self.set_temp + self.oor_temp_c and \
            self.humid >= self.set_humid - self.oor_humid_d and self.humid <= self.set_humid + self.oor_humid_d:
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

    def sense_th(self) :
        while True :
            try :
                self.humidity, self.temperature = Adafruit_DHT.read_retry(self.sensor, self.sensor_1)
                if math.isnan(self.humidity) == False and math.isnan(self.temperature) == False:
                    self.humid = self.humidity
                    self.temp = self.temperature
                    self.status_out()
                    print([self.humid,self.temp])

                    time.sleep(2)
                else :
                    print('Read value is NaN! Trying again...')
                    sleep(1)
            except TypeError as e:
                print("Reading from bme280 failure: ",e.args)
                time.sleep(1)
