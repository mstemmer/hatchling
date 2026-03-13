
import sys
import os
import yaml
import argparse
from time import sleep, strftime
from datetime import datetime
import logging
import __main__

# Parse arguments early to get species, init, and run flags
parser = argparse.ArgumentParser(prog='hatchling', add_help=False)
parser.add_argument('--init', dest='init', action='store_true', default=False)
parser.add_argument('--run', dest='run', action='store_true', default=False)
parser.add_argument('--species', metavar='', dest='species', type=str)
parser.add_argument('--silent', dest='silent', action='store_true', default=False)
parser.add_argument('--fixed_dc', metavar='', dest='fixed_dc', type=int)
early_args, remaining = parser.parse_known_args()

# Validate arguments
if early_args.init and early_args.run:
    print('ERROR: Cannot use both --init and --run flags together')
    sys.exit("--> Exiting program")

if early_args.init and early_args.species is None:
    print('ERROR: --species must be specified with --init')
    print('Usage: python hatchling.py --init --species chicken')
    sys.exit("--> Exiting program")

if early_args.run and early_args.species is not None:
    print('WARNING: --species is not needed with --run (will use saved species)')
    # Continue anyway, but will use the saved species from time_init.txt

# Determine data folder path early
hatchling_dir = str(os.path.dirname(os.path.realpath(__file__)))
data_folder = os.path.join(hatchling_dir, "data")
if not os.path.exists(data_folder):
    os.mkdir(data_folder)

# Determine init file path
time_init_file = os.path.join(data_folder, 'init.txt')

# Handle initialization
if early_args.init:
    # Creating new incubation
    time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Save both time_init and species in the file
    with open(time_init_file, 'w') as f:
        f.write(f"{time_str}|{early_args.species}")
    
    # Create species folder
    time_species_folder = f'{datetime.now().strftime("%Y-%m-%d")}_{early_args.species}'
    time_species_path = os.path.join(data_folder, time_species_folder)
    if not os.path.exists(time_species_path):
        os.mkdir(time_species_path)
    
    log_file_path = os.path.join(time_species_path, 'hatch.log')
    data_file_path = os.path.join(time_species_path, 'data.csv')
    
    # Delete old files if they exist (overwrite)
    for file_path in [log_file_path, data_file_path]:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                sleep(0.2)
            except OSError as e:
                print(f"WARNING: Could not delete {file_path}: {e}")
    
    # Create fresh log file
    max_attempts = 5
    for attempt in range(max_attempts):
        try:
            with open(log_file_path, 'w') as f:
                pass
            if os.path.exists(log_file_path):
                break
        except OSError as e:
            if attempt < max_attempts - 1:
                sleep(0.1 * (attempt + 1))
            else:
                print(f"ERROR: Could not create log file: {log_file_path}")
                sys.exit("--> Exiting program")
    
    print(f"✓ Initialized new incubation for {early_args.species}")
    print(f"✓ Created folder: {time_species_path}")
    print(f"✓ Ready to run: python hatchling.py --run")
    sys.exit(0)

# For --run and default (resume) mode, read existing time_init
if not os.path.exists(time_init_file):
    print('ERROR: No incubation initialized.')
    print('Please run initialization first:')
    print('  python hatchling.py --init --species chicken')
    sys.exit("--> Exiting program")

with open(time_init_file, 'r') as f:
    time_init_data = f.read().strip()

# Parse time_init and species from the file
if '|' in time_init_data:
    time_str, saved_species = time_init_data.split('|', 1)
else:
    # Backward compatibility: old format without species
    time_str = time_init_data
    saved_species = early_args.species

time_init = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')

# Use saved species from file, or override with command line if provided
species = early_args.species if early_args.species else saved_species

if not species:
    print('ERROR: Species not found. Please initialize first:')
    print('  python hatchling.py --init --species chicken')
    sys.exit("--> Exiting program")

# Determine status based on --run flag
run_status = "Starting incubation run" if early_args.run else "Resuming incubation"

# Determine log file path based on time_init and species
time_species_folder = f'{str(time_init.date())}_{species}'
time_species_path = os.path.join(data_folder, time_species_folder)

# Verify the species folder exists
if not os.path.exists(time_species_path):
    print(f'ERROR: Incubation folder not found: {time_species_path}')
    print('Please initialize first:')
    print(f'  python hatchling.py --init --species {species}')
    sys.exit("--> Exiting program")

log_file_path = os.path.join(time_species_path, 'hatch.log')

# Verify the log file exists
if not os.path.exists(log_file_path):
    print(f'ERROR: Log file not found: {log_file_path}')
    print('Please initialize first:')
    print(f'  python hatchling.py --init --species {species}')
    sys.exit("--> Exiting program")

# Set up logging with both file and console handlers
log_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Create a filter to suppress NumExpr messages
class NumExprFilter(logging.Filter):
    """Filter to suppress NumExpr-related log messages"""
    def filter(self, record):
        if 'NumExpr' in record.getMessage():
            return False
        if 'numexpr' in record.getMessage().lower():
            return False
        return True

numexpr_filter = NumExprFilter()

file_handler = logging.FileHandler(log_file_path)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)
file_handler.addFilter(numexpr_filter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(log_format)
console_handler.addFilter(numexpr_filter)

# Clear any existing handlers first
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# Configure logging with force=True to override any previous config
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO,
    handlers=[file_handler, console_handler],
    datefmt='%Y-%m-%d %H:%M:%S',
    force=True  # Force reconfiguration
)

from brood.spawn import SpawnHatchling
from brood.pico import fan_control


class Hatchling():
    def __init__(self):
        parser = argparse.ArgumentParser(prog='hatchling')
        parser.add_argument('--init', dest='init', action='store_true', default=False, help='Initialize new incubation')
        parser.add_argument('--run', dest='run', action='store_true', default=False, help='Start incubation run')
        parser.add_argument('--species', metavar='', dest='species', type=str, help='Species for incubation')
        parser.add_argument('--silent', dest='silent', action='store_true', default=False, help='Deactivate the alarm buzzer')
        parser.add_argument('--fixed_dc', metavar='', dest='fixed_dc', type=int, help='Ignores PID controller and sets heater to fixed duty cycle.')
        self.args = parser.parse_args()

        self.time_init = self.time_init()
        self.config = self.config()
        self.inc_program = self.inc_program()

        SpawnHatchling(self.config, self.inc_program, self.time_init, time_species_path, log_file_path)

        
    def time_init(self):
        # Already determined at module level
        return time_init


    def config(self):
        config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"settings.yml" )
        with open(config_path) as config_file:
            config = yaml.safe_load(config_file)

        # Track init mode in config
        config["init"] = self.args.init

        if self.args.silent == True:
            config["mode"] = config["silent_mode"]
            logging.info('Buzzer deactivated')
        else:
            config["mode"] = config["buzzer_mode"]

        if self.args.fixed_dc != None:
            config["fixed_dc"] = self.args.fixed_dc
        
        return config

    def inc_program(self):
        inc_program_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__)) ),"inc_program.yml" )
        with open(inc_program_path) as inc_program_file:
            inc_program = yaml.safe_load(inc_program_file)

        species_list = inc_program["species"]

        # Use species from module level (saved from init)
        if species not in species_list:
            print('Species not in list')
            sys.exit("--> Exiting program")
        else:
            inc_program = inc_program[species]
            return inc_program



# Only run Hatchling if this is the main process
if __name__ == '__main__':
    # Log startup messages - only in main process
    logging.info('Hatchling startup initiated')
    logging.info(f'{run_status} from time point: {time_init}')
    logging.info(f'Load incubation program: {species}')
    
    # Load config and set up fan
    config_path = os.path.join(str(os.path.dirname(os.path.realpath(__file__))), "settings.yml")
    with open(config_path) as config_file:
        temp_config = yaml.safe_load(config_file)
    
    # Control fan and flush logs before spawning
    logging.info(f'Fan control: set duty cycle to {temp_config["fan_speed"]}%')
    fan_control(temp_config["fan_speed"])
    
    for handler in logging.root.handlers:
        handler.flush()
    
    # Small delay to ensure file writes complete
    sleep(1.0)
    
    Hatchling()
