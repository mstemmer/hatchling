
import sys
import os
import yaml
import argparse
from time import sleep, strftime
from datetime import datetime
import logging

# Parse arguments early to get species and init flag
parser = argparse.ArgumentParser(prog='hatchling', add_help=False)
parser.add_argument('--init', dest='init', action='store_true', default=False)
parser.add_argument('--species', metavar='', dest='species', type=str)
parser.add_argument('--silent', dest='silent', action='store_true', default=False)
parser.add_argument('--fixed_dc', metavar='', dest='fixed_dc', type=int)
early_args, remaining = parser.parse_known_args()

# Determine data folder path early
hatchling_dir = str(os.path.dirname(os.path.realpath(__file__)))
data_folder = os.path.join(hatchling_dir, "data")
if not os.path.exists(data_folder):
    os.mkdir(data_folder)

# Determine time_init early
time_init_file = os.path.join(data_folder, 'time_init.txt')
if early_args.init:
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(time_init_file, 'w') as f:
        f.write(time_str)
else:
    with open(time_init_file, 'r') as f:
        time_str = f.read().strip()

time_init = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')

# Log resumption status
init_status = "Starting new incubation" if early_args.init else "Resuming incubation"

# Determine log file path early
time_species_folder = f'{str(time_init.date())}_{early_args.species}'
time_species_path = os.path.join(data_folder, time_species_folder)
if not os.path.exists(time_species_path):
    os.mkdir(time_species_path)

log_file_path = os.path.join(time_species_path, 'hatch.log')

# Delete log file if starting new incubation
if early_args.init and os.path.exists(log_file_path):
    os.remove(log_file_path)

# Set up logging with both file and console handlers from the start
log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    handlers=[file_handler, console_handler],
    datefmt='%Y-%m-%d %H:%M:%S'
)

from brood.spawn import SpawnHatchling
from brood.pico import fan_control

logging.info('Hatchling startup initiated')
logging.info(f'{init_status} from time point: {time_init}')

class Hatchling():
    def __init__(self):
        parser = argparse.ArgumentParser(prog='hatchling')
        # parser.add_argument('--samplesheet', dest='samples', metavar='', help='Please provide path to samplesheet (tsv format)')
        parser.add_argument('--init', dest='init', action='store_true', default=False, help='Start new incubation. Default: resume from last time point')
        parser.add_argument('--species', metavar='', dest='species', type=str, help='Load species specific incubation program: chicken, quail, elephant. See inc_program.yml')
        parser.add_argument('--silent', dest='silent', action='store_true', default=False, help='Deactivate the alarm buzzer')
        parser.add_argument('--fixed_dc', metavar='', dest='fixed_dc', type=int, help='Ignores PID controller and sets heater to fixed duty cycle.')
        self.args = parser.parse_args()

        self.time_init = self.time_init()
        self.config = self.config()
        self.inc_program = self.inc_program()

        fan_control(self.config["fan_speed"])

        SpawnHatchling(self.config, self.inc_program, self.time_init, time_species_path)

        
    def time_init(self):
        # Already determined at module level
        return time_init


    def config(self):
        config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"settings.yml" )
        with open(config_path) as config_file:
            config = yaml.safe_load(config_file)

        data_file_path = os.path.join(time_species_path, 'data.csv')

        if self.args.init == True: # decide if start new time or resume from file
            config["init"] = True
            if os.path.exists(data_file_path): # delete data file if init == True
                os.remove(data_file_path)

        if self.args.silent == True:
            config["mode"] = config["silent_mode"]
            logging.info('Buzzer deactivated')
        else:
            config["mode"] = config["buzzer_mode"]
        config["init"] = None

        if self.args.fixed_dc != None:
            config["fixed_dc"] = self.args.fixed_dc
        return config

    def inc_program(self):
        inc_program_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"inc_program.yml" )
        with open(inc_program_path) as inc_program_file:
            inc_program = yaml.safe_load(inc_program_file)

        species_list = inc_program["species"]

        if self.args.species == None:
            print('Species not specified, please see --help')
            sys.exit("--> Exiting program")
        elif self.args.species not in species_list:
            print('Species not in list')
            sys.exit("--> Exiting program")
        elif self.args.species in species_list:
            inc_program = inc_program[self.args.species]
            logging.info(f'Load incubation program: {self.args.species}')
            print(f'Load incubation program: {self.args.species}')
            return inc_program

if __name__ == '__main__':
    Hatchling()
