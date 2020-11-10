import sys
import os
import json
from time import sleep, strftime
from datetime import datetime
import math
import csv
from multiprocessing import Process, Queue


from controller import BroodController


if __name__ == '__main__':
    def config():
        config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"settings.json" )
        with open(config_path) as config_file:
            config = json.load(config_file)

        if os.path.exists(os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"])) is False:
                os.mkdir(os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"]))

        config["data_folder"]=os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"])
        config["mode"] = config["silent_mode"]

        return config

    def inc_program():
        inc_program_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"inc_program.json" )
        with open(inc_program_path) as inc_program_file:
            inc_program = json.load(inc_program_file)

        inc_program = inc_program["chicken"]["phase_1"]
        return inc_program

    def time_init():
        time = {}
        time['time_init'] = str(datetime.now())
        with open('time.json', 'w') as time_file:
            json.dump(time, time_file, indent=4)
        return time

    def run_controller(config, inc_program, q):
        BroodController(config, inc_program, q)
        # bc.status_out()


    config = config()
    inc_program = inc_program()
    time_init = time_init()

    # run_controller(config)

    q = Queue()
    processes = []
    p = Process(target=run_controller, args=(config, inc_program, q,) )
    p.start()
    p.join()

    # print(config)
    # print(time_init)
    # print(config['setup_pin']['latch'])
