
import sys
import RPi.GPIO as GPIO
from time import sleep, strftime
import time
from multiprocessing import Process, Pipe
import math
from datetime import datetime
import csv
import pidpy as PIDController
# from Adafruit_BME280 import BME280
import Adafruit_DHT
# import Adafruit_PureIO
# import bme280

#define the pins connecting to 74HC595
dataPin = 11      #DS Pin of 74HC595(Pin14)
latchPin = 13      #ST_CP Pin of 74HC595(Pin12)
clockPin = 15       #CH_CP Pin of 74HC595(Pin11)
mode = [0x3F, 0x2D, 0x35, 0x1D, 0x1D, 0x2B, 0x33, 0x1B, 0x1B, 0x2E, 0x36, 0x1E, 0x1E, 0x2E, 0x36, 0x1E, 0x1E] # w/o buzzer for testing
#mode = [0x3F, 0x2D, 0x35, 0x1D, 0x5D, 0x2B, 0x33, 0x1B, 0x5B, 0x2E, 0x36, 0x1E, 0x5E, 0x6E, 0x76, 0x5E, 0x5E] # with buzzer
LSBFIRST = 1 #Defines the data bit that is transmitted preferentially in the shift_out function.
MSBFIRST = 2

start_up_delay = 10

#set brood temperature & humidity plus out of range temperatures
brood_temp_1 = float(30) # 37.8°C - 38°C
brood_temp_2 = float(37) # 37°C
brood_humid_1 = float(57) # 55 - 60%
brood_humid_2 = float(85) # 80 - 90%
day_change_temp = 18 # from this day on set to different temperature
day_change_humid = 20 # from this day on set to different humidity
oor_temp_a = float(0.25)   #green
oor_temp_b = float(0.5)    #blue
oor_temp_c = float(1.5)      #red
oor_temp_d = float(20)      #red plus buzzer
oor_humid_a = float(2)     #green
oor_humid_b = float(5)     #blue
oor_humid_c = float(12)    #red
oor_humid_d = float(50)    #red plus buzzer

#controls the mosfet & heat element
heatPin = 7

# setup stepper motor; Vref set to 0.74V, with a 1.5A stepper
egg_turn_days = 17  # need to turn eggs 4 times per day until & including day 17 --> 68 times, every 6 hours
egg_turns = egg_turn_days * 4 +1
days_incub = 23 + 1 # 21 days to hatching, +1 for range function to include last day
eggTurnCycle = 1200 # 3600 seconds == 1 hour; 21600 seconds == 6 hours

stepPin = 31
sleepPin = 29
steps_per_round = 200  # Step angle is 1.8°, so 200 steps to complete the 360° in full step mode
# M0, M2 are pulled high with 3.3V to set Mode 101 --> 32 microsteps/step
# direction pin is not defined, need only one direction
step_count = steps_per_round * 32
step_delay = .0208 / 32  # controls the speed of the motor

def setup() :
    GPIO.setmode(GPIO.BOARD)       # Numbers GPIOs by physical location
    GPIO.setwarnings(False)
    GPIO.setup(dataPin, GPIO.OUT)
    GPIO.setup(latchPin, GPIO.OUT)
    GPIO.setup(clockPin, GPIO.OUT)
    GPIO.setup(heatPin, GPIO.OUT)
    GPIO.setup(sleepPin, GPIO.OUT)
    GPIO.setup(stepPin, GPIO.OUT)
    GPIO.output(heatPin, GPIO.LOW)

def get_time_now():     # get system time
    return datetime.now().strftime('%H:%M:%S')

def status_read(temp, humid, set_temp, set_humid) :
    if temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[1]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[2]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[3]
        return status
    elif temp >= set_temp - oor_temp_d and temp <= set_temp + oor_temp_d and \
        humid >= set_humid - oor_humid_a and humid <= set_humid + oor_humid_a:
        status = mode[4]
        return status
    elif temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[5]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[6]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[7]
        return status
    elif temp >= set_temp - oor_temp_d and temp <= set_temp + oor_temp_d and \
        humid >= set_humid - oor_humid_b and humid <= set_humid + oor_humid_b:
        status = mode[8]
        return status
    elif temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[9]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[10]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[11]
        return status
    elif temp >= set_temp - oor_temp_d and temp <= set_temp + oor_temp_d and \
        humid >= set_humid - oor_humid_c and humid <= set_humid + oor_humid_c:
        status = mode[12]
        return status
    elif temp >= set_temp - oor_temp_a and temp <= set_temp + oor_temp_a and \
        humid >= set_humid - oor_humid_d and humid <= set_humid + oor_humid_d:
        status = mode[13]
        return status
    elif temp >= set_temp - oor_temp_b and temp <= set_temp + oor_temp_b and \
        humid >= set_humid - oor_humid_d and humid <= set_humid + oor_humid_d:
        status = mode[14]
        return status
    elif temp >= set_temp - oor_temp_c and temp <= set_temp + oor_temp_c and \
        humid >= set_humid - oor_humid_d and humid <= set_humid + oor_humid_d:
        status = mode[15]
        return status
    else :
        status = mode[16]
        return status


def shift_out(dPin,cPin,order,val): #shift_out function, use bit serial transmission.
    for i in range(0,8):
        GPIO.output(cPin,GPIO.LOW);
        if(order == LSBFIRST):
            GPIO.output(dPin,(0x01&(val>>i)==0x01) and GPIO.HIGH or GPIO.LOW)
        elif(order == MSBFIRST):
            GPIO.output(dPin,(0x80&(val<<i)==0x80) and GPIO.HIGH or GPIO.LOW)
        GPIO.output(cPin,GPIO.HIGH);

def status_out(status): #74HC595 will update the data to the parallel output port.
    GPIO.output(latchPin,GPIO.LOW)  #Output low level to latchPin
    shift_out(dataPin,clockPin,LSBFIRST,status) #Send serial data to 74HC595
    GPIO.output(latchPin,GPIO.HIGH) #Output high level to latchPin
    time.sleep(0.1)

def count_days(conn) :
    for d in range(1, days_incub) :
        conn.send(d)
        sleep(86400) #1d = 86400 secs

def move_eggs(conn) :
    for m in range(1, egg_turns):
        GPIO.output(sleepPin, GPIO.HIGH)
        sleep(0.2) # wakeup time is min. 1 millisecond
        for x in range(step_count):
            GPIO.output(stepPin, GPIO.HIGH)
            sleep(step_delay)
            GPIO.output(stepPin, GPIO.LOW)
            sleep(step_delay)
        sleep(0.2)
        GPIO.output(sleepPin, GPIO.LOW) # put DRV8825 into sleep mode --> draws much less energy
        conn.send(m)
        time.sleep(eggTurnCycle)

def sense_th(conn) :
    # try:
    #     bme280_76 = BME280(address=0x76)
    #     print ("Sensor 1 is working (0x76)")
    #     bme280_77 = BME280(address=0x77)
    #     print ("Sensor 2 is working (0x77)")
    # except OSError as io:
    #     print('sensors are not responding! exiting program...', io.args)
    #     sys.exit("--> hit ctrl-c to return to terminal")
    sensor = Adafruit_DHT.DHT22
    pin = 12
    while True :
        try :
            # temp_1,pres_1,humid_1 = bme280.readBME280All(addr=0x76)
            # temp_2,pres_2,humid_2 = bme280.readBME280All(addr=0x77)
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
            # temp_2 = bme280_77.read_temperature()
            # humid_1 = bme280_76.read_humidity()
            # humid_2 = bme280_77.read_humidity()

            if math.isnan(humidity) == False and math.isnan(temperature) == False:
                conn.send([humidity,temperature])
                sleep(2)
            else :
                print('Read value is NaN! Trying again...')
                sleep(1)
        except TypeError as e:
            print("Reading from bme280 failure: ",e.args)
            sleep(1)


# PID settings
cycle_time = 1
k_param = 60
i_param = 40
d_param = 10
cal_time=300

def output(parent_sense_th, parent_day, parent_move) :
    # pid = PIDController.pidpy(cycle_time, k_param, i_param, d_param) #initialize PID controller
    heat = GPIO.PWM(heatPin, 200)
    heat.start(0)
    sleep(start_up_delay) # startup phase: this time is needed to let eggs move one time --> parent_move.poll(0.1) == True;
            # basically each process should have run once before the output process
    print("Reading sensors ...")
    for s in range(1,10000000) :
        sleep(cycle_time)

        try :
            if parent_day.poll(0.1)== True :
                d = parent_day.recv()
                #print('Day=' + str(d))

            elif parent_move.poll(0.1) == True :
                m = parent_move.recv()
                #print('eggTurn=' + str(m))

            else :
                humidity,temperature = parent_sense_th.recv()
                # temp_1 = round(temp_1, 2)
                # temp_2 = round(temp_2, 2)
                # temp = round(((temp_1 + temp_2) / 2), 2)
                #
                # humid_1 = round(humid_1, 2)
                # humid_2 = round(humid_2, 2)
                # humid = round(((humid_1 + humid_2) / 2), 2)

                if d < day_change_temp and d < day_change_humid and s <= cal_time:
                    set_temp = temperature
                    set_humid = humidity
                    # duty_cycle = pid.calcPID_reg4(temp, set_temp, True)
                    duty_cycle = 0
                    heat.ChangeDutyCycle(duty_cycle)
                    status_out(status_read(temperature, humidity, set_temp, set_humid))  # update LED & buzzer status according to meassured temperature & humidity

                elif d < day_change_temp and d < day_change_humid and s > cal_time:
                    set_temp = brood_temp_1
                    set_humid = brood_humid_1
                    # duty_cycle = pid.calcPID_reg4(temp, set_temp, True)
                    duty_cycle = 25
                    heat.ChangeDutyCycle(duty_cycle)
                    status_out(status_read(temperature, humidity, set_temp, set_humid))  # update LED & buzzer status according to meassured temperature & humidity




                elif d >= day_change_temp and d < day_change_humid :
                    set_temp = brood_temp_2
                    set_humid = brood_humid_1
                    duty_cycle = pid.calcPID_reg4(temp, set_temp, True)
                    heat.ChangeDutyCycle(duty_cycle)
                    status_out(status_read(temp, humid, set_temp, set_humid))

                else :
                    set_temp = brood_temp_2
                    set_humid = brood_humid_2
                    duty_cycle = pid.calcPID_reg4(temp, set_temp, True)
                    heat.ChangeDutyCycle(duty_cycle)
                    status_out(status_read(temp, humid, set_temp, set_humid))

                print('Day=' + str(d) + ' eggs_turned=' + str(m) + ' ' + get_time_now() + ' outCycle=' + str(s)
                      + ' Temp_avg: ' + str(temperature)  + ' Humidity: ' + str(humidity) + ' duty_cycle: ' + str(duty_cycle))
                #sleep(2)
                row = [d, m, get_time_now(), temperature, humidity, duty_cycle]
                with open('data/output_1108.csv', 'a', newline='') as csvfile:
                    dhtwriter = csv.writer(csvfile)
                    dhtwriter.writerow(row)
                csvfile.close()

        except OSError as f:
            print('output error: ', f.args)

def destroy():
    #heat = GPIO.PWM(heatPin, 100)
    #heat.stop()
    status=mode[0]
    status_out(status)
    GPIO.output(heatPin, GPIO.LOW)
    #GPIO.cleanup()

def main():
    print ('Program is setting up ... please wait')
    setup()
    try:
        sense_thPipeIn, sense_th_PipeOut = Pipe()
        dayPipeIn, day_PipeOut = Pipe()
        movePipeIn, move_PipeOut = Pipe()

        p1 = Process(target=count_days, args=[dayPipeIn])
        p2 = Process(target=move_eggs, args=[movePipeIn])
        p3 = Process(target=sense_th, args=[sense_thPipeIn])
        p4 = Process(target=output, args=[sense_th_PipeOut, day_PipeOut, move_PipeOut])
        p1.start()
        p2.start()
        p3.start()
        p4.start()
        p1.join()
        p2.join()
        p3.join()
        p4.join()
        destroy()
        sys.exit("Program completed! --> hit ctrl-c to return to terminal")
    except KeyboardInterrupt:
        p1.terminate()
        p2.terminate()
        p3.terminate()
        p4.terminate()
        destroy()
        print("Program interrupted")

if __name__ == '__main__':
    main()
