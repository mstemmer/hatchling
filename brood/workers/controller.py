from RPi import GPIO # Now imports from system, not conda
from brood.workers.PT100_sensor import PT100TempSense
from brood.pico import fan_control
import board
from multiprocessing import Process, Queue
import adafruit_dht as Adafruit_DHT
# import pidpy as PIDController
from simple_pid import PID
import string
import time
import math
import sys
import logging

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
        # GPIO.setwarnings(False)

        # initi humidity and temperature sensors
        self.sensor_humid = config['setup_pin']['DHT22_sensor']
        # self.sensor_2 = config['setup_pin']['sensor_2']
        self.DHT22 = Adafruit_DHT.DHT22(getattr(board, f"D{self.sensor_humid}"))

        # self.temp_0 = PT100TempSense(0)
        # self.temp_1 = PT100TempSense(1)

        self.data_pin = config['setup_pin']['data']
        self.latch_pin = config['setup_pin']['latch']   
        self.clock_pin = config['setup_pin']['clock']

        self.heat_pin = config['setup_pin']['heat']
        self.config = config

        pins = [self.data_pin, self.latch_pin, self.clock_pin, self.heat_pin]

        for p in pins :
            GPIO.setup(p, GPIO.OUT)
        GPIO.output(self.heat_pin, GPIO.HIGH)

        logging.info('Initializing PID controller')
        print('Initializing PID controller')
        self.pid = PID(290, 70, 10, setpoint=37) # init pid controller 290, 70, 10
        self.pid.output_limits = (0, 100)
        self.pid.sample_time = None
        self.pid.tunings = (config["PID_parameters"]) # update PID controller with config parameters
        # self.pid.proportional_on_measurement = True

        self.heat = GPIO.PWM(self.heat_pin, 100)
        self.heat.start(0)
        

        if 'fixed_dc' in self.config: # check if exists
            logging.info(f'PID controller is deactivated and duty cycle fixed to {self.config["fixed_dc"]}')
            print(f'PID controller is deactivated and duty cycle fixed to {self.config["fixed_dc"]}')

        # init class
        self.set_humid, self.set_temp = [55, 36]
        self.q_data = q_data
        self.q_prog = q_prog
        self.control()

    def read_program(self): #read incubation program sent by BroodLord
        if self.q_prog.empty() != True:
            self.set_humid, self.set_temp = self.q_prog.get()
            self.pid.setpoint = self.set_temp # update set_temp within pid controller
            logging.info('Controller received updated parameters')
            print('Controller received updated parameters')
        else:
            pass

        self.oor_temp_high = []
        self.oor_temp_low = []
        self.oor_humid_high = []
        self.oor_humid_low = []

        for val in range(3):
            temp_high = self.set_temp + self.config['LED_status']['oor_temp'][val]
            temp_low = self.set_temp - self.config['LED_status']['oor_temp'][val]
            humid_high = self.set_humid + self.config['LED_status']['oor_humid'][val]
            humid_low = self.set_humid - self.config['LED_status']['oor_humid'][val]
            self.oor_temp_high.append(temp_high)
            self.oor_temp_low.append(temp_low)
            self.oor_humid_high.append(humid_high)
            self.oor_humid_low.append(humid_low)

    def pid_controller(self, curr_value):
        if 'fixed_dc' in self.config: # check if exists
            self.duty_cycle = self.config["fixed_dc"]
        else:
            self.duty_cycle = self.pid(curr_value)
        # print(self.duty_cycle)
        # duty_cycle = 0
        # p, i, d = self.pid.components
        # print(p, i, d)
        self.heat.ChangeDutyCycle(self.duty_cycle)

    def read_temperature(self, sensor):
        try:
            temperature = PT100TempSense(sensor).get_temp()
        except TypeError as e:
                    logging.error("Reading from PT100 failure!")
                    print("Reading from PT100 failure: ",e.args)
                    time.sleep(2)
        return temperature


    def read_humidity(self):
        try:
            humidity = self.DHT22.humidity
        except TypeError as e:
                    logging.error("Reading from DHT22 failure!")
                    print("Reading from DHT22 failure: ",e.args)
                    time.sleep(2)
        return humidity
    

    def control(self):
        try:
            h = 20 # initial value, because humidity is not available at the beginning
            delay = time.time()
            while True:
                self.read_program()
                temp_0 = self.read_temperature(0)
                time.sleep(0.1)
                temp_1 = self.read_temperature(1)
                if time.time() - delay >= 20: # humidity is read every 20 seconds
                    h = self.read_humidity()
                    delay = time.time()

                if all(not math.isnan(x) for x in [h, temp_0, temp_1]):
                    if 10 < h < 70 and 10 < temp_0 < 70 and 10 < temp_1 < 70:

                        current_temperature = round((temp_0 + temp_1) / 2, 3)
                        current_humidity = round(h, 2)
                        
                        # self.status_out() # not needed right now, because no shift register
                        self.pid_controller(current_temperature)
                        # print(self.temp)

                        humid_raw, temp_raw, sens = 2, 3, 8 ##only for debug ,remove later
                        self.q_data.put([current_humidity, current_temperature, round(temp_0, 4), round(temp_1, 4), sens,
                        self.set_humid, self.set_temp, self.duty_cycle])

                        # time.sleep(1) # this way each sensor is read only every 2 seconds as per datasheet
                    else:
                        logging.error(f'Bad sensor read!')
                        print('Bad sensor read. Trying again...')
                        time.sleep(2)
                else :
                    logging.error('Read value is NaN!')
                    print('Read value is NaN! Trying again...')
                    time.sleep(2)
                continue

        except KeyboardInterrupt:
            self.heat.ChangeDutyCycle(0)
            fan_control(0)
            GPIO.output(self.heat_pin, GPIO.LOW)
            self.status_end()
            logging.info('Shutting down heater')
            logging.info('Close program')
            print('Shutting down heater')
            sys.exit('Close program')


    # def status_temp(self):
    #     if self.oor_temp_low[0] <= self.temp <= self.oor_temp_high[0]: #green
    #         return 0
    #     elif self.oor_temp_low[1] <= self.temp <= self.oor_temp_high[1]: #blue
    #         return 1
    #     elif self.oor_temp_low[2] <= self.temp <= self.oor_temp_high[2]: #red
    #         return 2
    #     elif self.oor_temp_low[2] >= self.temp or self.oor_temp_high[2] <= self.temp: # red buzzer
    #         return 3

    # def status_humid(self):
    #     if self.oor_humid_low[0] <= self.humid <= self.oor_humid_high[0]:
    #         return 0
    #     elif self.oor_humid_low[1] <= self.humid <= self.oor_humid_high[1]:
    #         return 1
    #     elif self.oor_humid_low[2] <= self.humid <= self.oor_humid_high[2]:
    #         return 2
    #     elif self.oor_humid_low[2] >= self.humid or self.oor_humid_high[2] <= self.humid:
    #         return 3

    # def status_read(self):
    #     status_temp = self.status_temp()
    #     status_humid = self.status_humid()

    #     if status_temp == 0 and status_humid == 0:
    #         self.status = self.config['mode'][1]
    #         return self.status

    #     elif status_temp == 1 and status_humid == 0:
    #         self.status = self.config['mode'][2]
    #         return self.status

    #     elif status_temp == 2 and status_humid == 0:
    #         self.status = self.config['mode'][3]
    #         return self.status

    #     elif status_temp == 3 and status_humid == 0:
    #         self.status = self.config['mode'][4]
    #         return self.status

    #     elif status_temp == 0 and status_humid == 1:
    #         self.status = self.config['mode'][5]
    #         return self.status

    #     elif status_temp == 1 and status_humid == 1:
    #         self.status = self.config['mode'][6]
    #         return self.status

    #     elif status_temp == 2 and status_humid == 1:
    #         self.status = self.config['mode'][7]
    #         return self.status

    #     elif status_temp == 3 and status_humid == 1:
    #         self.status = self.config['mode'][8]
    #         return self.status

    #     elif status_temp == 0 and status_humid == 2:
    #         self.status = self.config['mode'][9]
    #         return self.status

    #     elif status_temp == 1 and status_humid == 2:
    #         self.status = self.config['mode'][10]
    #         return self.status

    #     elif status_temp == 2 and status_humid == 2:
    #         self.status = self.config['mode'][11]
    #         return self.status

    #     elif status_temp == 3 and status_humid == 2:
    #         self.status = self.config['mode'][12]
    #         return self.status

    #     elif status_temp == 0 and status_humid == 3:
    #         self.status = self.config['mode'][13]
    #         return self.status

    #     elif status_temp == 1 and status_humid == 3:
    #         self.status = self.config['mode'][14]
    #         return self.status

    #     elif status_temp == 2 and status_humid == 3:
    #         self.status = self.config['mode'][15]
    #         return self.status

    #     else :
    #         self.status = self.config['mode'][16]
    #         return self.status

    # def shift_out(self): #shift_out function, use bit serial transmission
    #     val = self.status_read()
    #     for i in range(0,8):
    #         GPIO.output(self.clock_pin,GPIO.LOW)
    #         GPIO.output(self.data_pin,(0x01&(val>>i)==0x01) and GPIO.HIGH or GPIO.LOW)
    #         GPIO.output(self.clock_pin,GPIO.HIGH)

    # def status_out(self): #74HC595 will update the data to the parallel output port.
    #     GPIO.output(self.latch_pin,GPIO.LOW)  #Output low level to latchPin
    #     self.shift_out() #Send serial data to 74HC595
    #     GPIO.output(self.latch_pin,GPIO.HIGH) #Output high level to latchPin
    #     time.sleep(0.1)

    # def shift_end(self): #shift_out function, use bit serial transmission
    #     status = self.config['mode'][0]
    #     val = status
    #     for i in range(0,8):
    #         GPIO.output(self.clock_pin,GPIO.LOW)
    #         GPIO.output(self.data_pin,(0x01&(val>>i)==0x01) and GPIO.HIGH or GPIO.LOW)
    #         GPIO.output(self.clock_pin,GPIO.HIGH)

    # def status_end(self): #74HC595 will update the data to the parallel output port.
    #     GPIO.output(self.latch_pin,GPIO.LOW)  #Output low level to latchPin
    #     self.shift_end() #Send serial data to 74HC595
    #     GPIO.output(self.latch_pin,GPIO.HIGH) #Output high level to latchPin
    #     time.sleep(0.1)
