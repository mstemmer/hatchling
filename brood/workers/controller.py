from gpiozero import PWMLED
from brood.workers.temp_sensors.PT100_sensor import PT100TempSense
from brood.pico import fan_control
import board
from multiprocessing import Process, Queue
import adafruit_htu31d
# import pidpy as PIDController
from simple_pid import PID
import string
import time
import math
import sys
import logging


# Initialize custom PHASE logging level
import brood.logging_config

class BroodController():
    """ Reads data from two DHT22 sensors in a while loop. Reading alternates
    between the two sensors. Data is averaged over both, rounded and sent
    out via Queue(). Read values are checked for being numbers and loop is
    protected against read failures ocurring with DHT22 from time to time.
    This function also sets the status LEDs and regulates the heater
    automatically using a PID controller. The set_values are constantly
    evaluated."""

    def __init__(self, config, q_prog, q_data):
        # Use gpiozero PWMLED - works in forked processes with software PWM
        # Set pin factory to None to let gpiozero auto-select the best available
        from gpiozero import Device
        Device.pin_factory = None  # Auto-detect best factory
        
        # Initialize heater PWM on GPIO12
        self.heat = PWMLED(config['setup_pin']['heat'])
        self.heat.off()  # Start with heater off

        # initi humidity and temperature sensors
        # self.sensor_humid = config['setup_pin']['DHT22_sensor']
        # self.sensor_2 = config['setup_pin']['sensor_2']
        # self.DHT22 = Adafruit_DHT.DHT22(getattr(board, f"D{self.sensor_humid}"))

        # self.temp_0 = PT100TempSense(0)
        # self.temp_1 = PT100TempSense(1)

        # self.data_pin = config['setup_pin']['data']
        # self.latch_pin = config['setup_pin']['latch']   
        # self.clock_pin = config['setup_pin']['clock']

        
        self.config = config
        self.duty_cycle = 0

        # pins = [self.data_pin, self.latch_pin, self.clock_pin, self.heat_pin]
        
        # Initialize I2C and HTU31D sensors
        i2c = board.I2C()  # uses board.SCL and board.SDA

        # Initialize first sensor (default I2C address 0x40)
        self.htu0 = None
        self.sensor0_active = False
        try:
            self.htu0 = adafruit_htu31d.HTU31D(i2c, address=0x40)
            logging.info("Found HTU31D Sensor 0 with serial number %s", hex(self.htu0.serial_number))
            self.sensor0_active = True
        except Exception as e:
            logging.warning("Failed to initialize Sensor 0: %s", str(e))

        # Initialize second sensor (alternative I2C address 0x41 - requires address pin configured)
        self.htu1 = None
        self.sensor1_active = False
        try:
            self.htu1 = adafruit_htu31d.HTU31D(i2c, address=0x41)
            logging.info("Found HTU31D Sensor 1 with serial number %s", hex(self.htu1.serial_number))
            self.sensor1_active = True
        except Exception as e:
            logging.warning("Failed to initialize Sensor 1: %s", str(e))
        
        if not self.sensor0_active and not self.sensor1_active:
            logging.error("No sensors available! Cannot continue.")
            raise RuntimeError("Both sensors failed to initialize")

        # Initialize PID controller
        logging.info('Initializing PID controller')
        self.pid = PID(config["PID_parameters"][0], config["PID_parameters"][1], config["PID_parameters"][2], setpoint=37.8)
        self.pid.output_limits = (0, 100)
        self.pid.sample_time = 1.0  # Update PID every 1 second to avoid integral windup
        self.pid.tunings = (config["PID_parameters"]) # update PID controller with config parameters
        # self.pid.proportional_on_measurement = True

        if 'fixed_dc' in self.config: # check if exists
            logging.info(f'PID controller is deactivated and duty cycle fixed to {self.config["fixed_dc"]}')

        # init class
        self.set_humid, self.set_temp = [55, 37.8]
        self.q_data = q_data
        self.q_prog = q_prog
        self.control()

    def read_program(self): #read incubation program sent by BroodLord
        if self.q_prog.empty() != True:
            self.set_humid, self.set_temp = self.q_prog.get()
            self.pid.setpoint = self.set_temp # update set_temp within pid controller
            logging.info('Controller received updated parameters')
        else:
            pass

        # self.oor_temp_high = []
        # self.oor_temp_low = []
        # self.oor_humid_high = []
        # self.oor_humid_low = []

        # for val in range(3):
        #     temp_high = self.set_temp + self.config['LED_status']['oor_temp'][val]
        #     temp_low = self.set_temp - self.config['LED_status']['oor_temp'][val]
        #     humid_high = self.set_humid + self.config['LED_status']['oor_humid'][val]
        #     humid_low = self.set_humid - self.config['LED_status']['oor_humid'][val]
        #     self.oor_temp_high.append(temp_high)
        #     self.oor_temp_low.append(temp_low)
        #     self.oor_humid_high.append(humid_high)
        #     self.oor_humid_low.append(humid_low)

    def pid_controller(self, curr_value):
        """Update PWM duty cycle using PID controller"""
        if 'fixed_dc' in self.config:
            self.duty_cycle = self.config["fixed_dc"]
        else:
            self.duty_cycle = self.pid(curr_value)
        
        # gpiozero uses 0.0-1.0 range, convert from 0-100
        self.heat.value = self.duty_cycle / 100.0

    
    def read_HTU31D_0(self):
        if not self.sensor0_active:
            return float('nan'), float('nan')
        try:
            temperature, humidity = self.htu0.measurements
            return temperature, humidity
        except Exception as e:
            logging.error("Reading from HTU31D_0 failure: %s", str(e))
            self.sensor0_active = False  # Mark sensor as inactive
            return float('nan'), float('nan')

    def read_HTU31D_1(self):
        if not self.sensor1_active:
            return float('nan'), float('nan')
        try:
            temperature, humidity = self.htu1.measurements
            return temperature, humidity
        except Exception as e:
            logging.error("Reading from HTU31D_1 failure: %s", str(e))
            self.sensor1_active = False  # Mark sensor as inactive
            return float('nan'), float('nan')


    def control(self):
        try:
            while True:
                self.read_program()
                temp_0, humid_0 = self.read_HTU31D_0()
                time.sleep(0.1)
                temp_1, humid_1 = self.read_HTU31D_1()
                time.sleep(0.1)

                # Count how many valid readings we have
                valid_temps = [t for t in [temp_0, temp_1] if not math.isnan(t)]
                valid_humids = [h for h in [humid_0, humid_1] if not math.isnan(h)]
                
                # Need at least one valid sensor reading to continue
                if valid_temps and valid_humids:
                    # Check if values are in reasonable range
                    temps_in_range = all(10 < t < 70 for t in valid_temps)
                    humids_in_range = all(10 < h < 70 for h in valid_humids)
                    
                    if temps_in_range and humids_in_range:
                        # Average available values
                        temperature = round(sum(valid_temps) / len(valid_temps), 3)
                        humidity = round(sum(valid_humids) / len(valid_humids), 3)
                        
                        # Log if using degraded mode (only one sensor)
                        if len(valid_temps) == 1:
                            logging.warning("Operating in degraded mode: only one temperature sensor available")
                        if len(valid_humids) == 1:
                            logging.warning("Operating in degraded mode: only one humidity sensor available")

                        self.pid_controller(temperature)

                        self.q_data.put([temperature, humidity, round(temp_0, 4), round(temp_1, 4), 
                                        round(humid_0, 4), round(humid_1, 4), self.set_humid, 
                                        self.set_temp, self.duty_cycle])
                    else:
                        logging.error('Bad sensor read - values out of range!')
                        time.sleep(2)
                else:
                    logging.error('All sensors returned invalid readings (NaN)!')
                    time.sleep(2)
                continue

        except KeyboardInterrupt:
            self.heat.off()  # Stop PWM signal
            fan_control(0)
            # self.status_end()
            logging.info('Shutting down heater')
            logging.info('Close program')
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
