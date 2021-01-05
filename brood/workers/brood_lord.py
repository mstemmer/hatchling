from multiprocessing import Process, Queue
from time import sleep, strftime
import os
import json
from datetime import timedelta, datetime
from apscheduler.schedulers.background import BlockingScheduler
import RPi.GPIO as GPIO
import logging
# import datetime

class BroodLord():
    '''Reads the environmental set points, schedules their updates and sends them
    via queue() to controller. Class also controls the egg moving depending in config.
    Stepper driver was set to Vref: 0.74V with a 1.5A stepper motor. This model's
    step angle is 1.8°, so 200 steps are needed to complete a round in full step mode.
    Step mode was set to 101 (32 microsteps/step) by pulling up M0 and M2 pins.
    Step delay identified according to step angle. Direction pin is not defined.
    Driver is set to sleep after each moving to save energy and lower usage time.
    '''

    def __init__(self, config, inc_program, q_prog, time_init):
        GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by physical location
        GPIO.setwarnings(False)

        # get pins for stepper & setup
        self.step_pin = config["setup_pin"]["step"]
        self.sleep_pin = config["setup_pin"]["sleep"]
        pins = [self.step_pin, self.sleep_pin]
        for p in pins :
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, GPIO.LOW)

        steps_per_round = config["steps"]
        self.step_count = steps_per_round * 32 # a full round in Mode 101
        self.step_delay = .0208 / 32  # controls the speed of the motor

        # read config files
        self.q_prog = q_prog
        self.inc_program = inc_program
        self.time_init = time_init

        self.q_prog.put(inc_program["default_phase"]) # send standard inc_program to controller
        logging.info("Setting controller to default parameters")
        print("Setting controller to default parameters")

        scheduler = BlockingScheduler() # init scheduler

        # define timepoints of incubation phase changes relative to time_init
        if inc_program["phases"] > 1:
            logging.info("Additional phases found and added to scheduler")
            print("Additional phases found and added to scheduler")
            phase_changes = inc_program["phases"] - 1
            for p in range(phase_changes):
                phase = time_init + timedelta(days=inc_program["phase_changes"][p])

                # add job to scheduler
                scheduler.add_job(self.next_phase, args=(p, ), trigger='date',
                next_run_time=phase)
                logging.info(f'Controller update will occur on datetime: {phase}')
                print(f'Controller update will occur on datetime: {phase}')

        #  set scheduler to interval until end point of egg moving, relative to time_init
        if inc_program["activate_move_eggs"] == 1: # check if eggs should be moved
            scheduler.add_job(self.move_eggs, trigger='interval',
            hours = inc_program["interval_move_eggs"],
            start_date = datetime.now(),
            end_date= time_init + timedelta(days=inc_program["days_move_eggs"]))
            logging.info(f'Egg moving is activated and scheduled every {inc_program["interval_move_eggs"]} hours')
            print(f'Egg moving is activated and scheduled every {inc_program["interval_move_eggs"]} hours')
            self.move_eggs() # move eggs once at start

        # scheduler.print_jobs()
        scheduler.start()

    def next_phase(self, p):
        set_prog = self.inc_program["next_phase"][p]
        self.q_prog.put(set_prog)

    def move_eggs(self) :
        logging.info('Moving eggs')
        print('Moving eggs')

        GPIO.output(self.sleep_pin, GPIO.HIGH)
        sleep(0.2) # wakeup time is min. 1 millisecond
        for x in range(self.step_count):
            GPIO.output(self.step_pin, GPIO.HIGH)
            sleep(self.step_delay)
            GPIO.output(self.step_pin, GPIO.LOW)
            sleep(self.step_delay)
        sleep(0.2)
        GPIO.output(self.sleep_pin, GPIO.LOW) # put DRV8825 into sleep mode --> draws much less energy
