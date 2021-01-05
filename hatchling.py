from brood.spawn import SpawnHatchling
import sys
import os
import json
import argparse
from time import sleep, strftime
from datetime import datetime
import logging


class Hatchling():
    def __init__(self):
        parser = argparse.ArgumentParser(prog='hatchling')
        # parser.add_argument('--samplesheet', dest='samples', metavar='', help='Please provide path to samplesheet (tsv format)')
        parser.add_argument('--init', dest='init', action='store_true', default=False, help='Start new incubation. Default: resume from last time point')
        parser.add_argument('--species', metavar='', dest='species', type=str, help='Load species specific incubation program: chicken, quail, elephant. See inc_program.json')
        parser.add_argument('--silent', dest='silent', action='store_true', default=False, help='Deactivate the alarm buzzer')
        parser.add_argument('--fixed_dc', metavar='', dest='fixed_dc', type=int, help='Ignores PID controller and sets heater to fixed duty cycle.')
        self.args = parser.parse_args()

        self.time_init = self.time_init()
        self.config = self.config()
        self.inc_program = self.inc_program()

        SpawnHatchling(self.config, self.inc_program, self.time_init)


    def time_init(self):
        if self.args.init == True: # decide if start new time or resume from file
            time = {}
            time['time_init'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('time_init.json', 'w') as time_file:
                json.dump(time, time_file, indent=4)
            time = time["time_init"]
            time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S') # make sure time is saved as datetime object
            print(f'Starting new incubation. Time: {time}')
            return time
        else:
            with open('time_init.json', 'r') as time_file:
                time = json.load(time_file)
                time = time["time_init"]
                time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S') # make sure time is saved as datetime object
                print(f'Resuming from time point: {time}')
                return time


    def config(self):
        config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"settings.json" )
        with open(config_path) as config_file:
            config = json.load(config_file)

        if os.path.exists(os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"])) is False:
                os.mkdir(os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"]))
        config["data_folder"]=os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"])

        data_file = f'{str(self.time_init.date())}_{config["data_file"]}.csv'
        data_file_path = os.path.join(config["data_folder"], data_file)

        log_file = f'{str(self.time_init.date())}_{config["log_file"]}.txt'
        log_file_path = os.path.join(config["data_folder"], log_file) # get path for log file


        if self.args.init == True: # decide if start new time or resume from file
            config["init"] = True
            if os.path.exists(data_file_path): # delete data file if init == True
                os.remove(data_file_path)
            if os.path.exists(log_file_path): # delete log file if init == True
                os.remove(log_file_path)

        logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', level=logging.INFO, \
        filename=f'{log_file_path}', datefmt='%Y-%m-%d %H:%M:%S')

        if self.args.silent == True:
            config["mode"] = config["silent_mode"]
            logging.info('Buzzer deactivated')
            print('Buzzer deactivated')
        else:
            config["mode"] = config["buzzer_mode"]
        config["init"] = None

        if self.args.fixed_dc != None:
            config["fixed_dc"] = self.args.fixed_dc
        return config

    def inc_program(self):
        inc_program_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"inc_program.json" )
        with open(inc_program_path) as inc_program_file:
            inc_program = json.load(inc_program_file)

        species_list = inc_program["species"]

        if self.args.species == None:
            print('Species not specified, please see --help')
            sys.exit("--> Exiting program")
        elif self.args.species not in species_list:
            print('Species not in list')
            sys.exit("--> Exiting program")
        elif self.args.species == 'chicken':
            inc_program = inc_program["chicken"]
            logging.info('Load incubation program: chicken')
            print('Load incubation program: chicken')
            return inc_program


if __name__ == '__main__':
    Hatchling()
