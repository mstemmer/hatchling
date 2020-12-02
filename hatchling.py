from spawn import SpawnHatchling
import sys
import os
import json
import argparse
from time import sleep, strftime
from datetime import datetime


class Hatchling():
    def __init__(self):

        parser = argparse.ArgumentParser(prog='hatchling')
        # parser.add_argument('--samplesheet', dest='samples', metavar='', help='Please provide path to samplesheet (tsv format)')
        parser.add_argument('-i', '--init', dest='init', action='store_true', default=False, help='Initialize incubation program.')
        parser.add_argument('-s', '--species', metavar='', dest='species', type=str, help='Load species specific incubation program.')
        # parser.add_argument('--gene_names_off', dest='gn_off', action='store_true', default=False, help='Do not change gene_ID with gene_name.')
        self.args = parser.parse_args()

        self.config = self.config()
        self.inc_program = self.inc_program()
        self.time_init = self.time_init()

        SpawnHatchling(self.config, self.inc_program, self.time_init)

    def config(self):
        config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"settings.json" )
        with open(config_path) as config_file:
            config = json.load(config_file)

        if os.path.exists(os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"])) is False:
                os.mkdir(os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"]))

        config["data_folder"]=os.path.join(str(os.path.dirname(os.path.realpath(__file__))),config["data_folder"])
        config["mode"] = config["silent_mode"]

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
            print('Load incubation program: chicken')
            return inc_program


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


if __name__ == '__main__':
    Hatchling()
