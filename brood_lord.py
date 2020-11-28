from multiprocessing import Process, Queue
from time import sleep, strftime
import os
import json
from datetime import timedelta, datetime
from apscheduler.schedulers.background import BlockingScheduler
import RPi.GPIO as GPIO
# import datetime

class BroodLord():

    def __init__(self, inc_program, q_prog, time_init):
        GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by physical location
        GPIO.setwarnings(False)

        # get pins for stepper
        config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"settings.json" )
        with open(config_path) as config_file:
            config = json.load(config_file)

        self.step_pin = config["setup_pin"]["step"]
        self.sleep_pin = config["setup_pin"]["sleep"]

        pins = [self.step_pin, self.sleep_pin]

        for p in pins :
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.LOW)


        # identify step_delay according to step angle # setup stepper motor; Vref set to 0.74V, with a 1.5A stepper
        steps_per_round = 200  # Step angle is 1.8°, so 200 steps to complete the 360° in full step mode
        # M0, M2 are pulled high with 3.3V to set Mode 101 --> 32 microsteps/step
        # direction pin is not defined, need only one direction
        self.step_count = steps_per_round * 32 # to complete a full round in Mode 101
        self.step_delay = .0208 / 32  # controls the speed of the motor


        self.q_prog = q_prog
        self.inc_program = inc_program
        self.time_init = time_init

        print(f'Time init: {time_init}')

        self.q_prog.put(inc_program["default_phase"])
        print("Setting controller to default parameters")

        scheduler = BlockingScheduler() # init scheduler

        # define timepoints of incubation phase changes relative to time_init
        if inc_program["phases"] > 1:
            print("Additional phases found and added to scheduler")
            phase_changes = inc_program["phases"] - 1
            phase_changes_time = []
            for p in range(phase_changes):
                phase = time_init + timedelta(days=inc_program["phase_changes"][p])
                phase_changes_time.append(phase)

            # add phase jobs
            for p in range(phase_changes):
                scheduler.add_job(self.next_phase, args=(p, ), trigger='date', next_run_time=phase_changes_time[p])


        #  define timepoints of egg moving relative to time_init
        if inc_program["activate_move_eggs"] == 1: # check if eggs should be moved
            print("Turning eggs activated and loaded into scheduler")
            egg_moves_per_day = 24 / inc_program["interval_move_eggs"]
            egg_moves = int(inc_program["days_move_eggs"] * egg_moves_per_day)
            egg_moves_time = []
            for m in range(1, egg_moves + 1):
                move = time_init + (timedelta(hours=inc_program["interval_move_eggs"]) * m)
                egg_moves_time.append(move)

            # add egg move jobs
            for m in range(egg_moves):
                scheduler.add_job(self.move_eggs, args=(m, ), trigger='date', next_run_time=egg_moves_time[m])

        scheduler.start()


    def next_phase(self, p):
        set_prog = self.inc_program["next_phase"][p]
        self.q_prog.put(set_prog)

    def next_move_eggs(self, m):
        print('Moving eggs', m)




    def move_eggs(self, m) :
        print('Moving eggs', m)

        GPIO.output(self.sleep_pin, GPIO.HIGH)
        sleep(0.2) # wakeup time is min. 1 millisecond
        for x in range(self.step_count):
            GPIO.output(self.step_pin, GPIO.HIGH)
            sleep(self.step_delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            sleep(self.step_delay)
        sleep(0.2)
        GPIO.output(self.sleep_pin, GPIO.LOW) # put DRV8825 into sleep mode --> draws much less energy
