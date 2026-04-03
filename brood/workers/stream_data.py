import time
from datetime import datetime, timedelta
import csv
import os
import sys
import subprocess
import pandas as pd
import logging

# Initialize custom PHASE logging level
import brood.logging_config


class Output():

    def __init__(self, config, q_data, time_init, data_folder):
        self.data_folder = data_folder
        self.config = config
        self.time_init = time_init
        self.q_data = q_data
        self.monitor_proc = None
        self.monitor_started = False
        
        # Track current day for daily file rotation
        self.current_day = datetime.now().date()
        self.next_rotation_time = self.time_init + timedelta(days=1)
        
        # Create CSV file and write headers
        self.file_path = self._create_file()
        time.sleep(0.5)
        
        # Start monitor process
        self._start_monitor()
        
        # Start streaming data
        self.output()

    def _create_file(self):
        """Create data folder and CSV file with headers, using symlink for data.csv"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        dated_file = f'data_{current_date}.csv'
        symlink_file = 'data.csv'
        
        dated_file_path = os.path.join(self.data_folder, dated_file)
        symlink_path = os.path.join(self.data_folder, symlink_file)
        
        # Write header if dated file doesn't exist
        if not os.path.exists(dated_file_path):
            with open(dated_file_path, 'w', newline='') as csvfile:
                data_writer = csv.writer(csvfile)
                header = ["Time", "Temperature", "Humidity", "Temp_0", "Temp_1", "Humid_0", "Humid_1", "Set_Temp", "Set_Humid", "Duty_Cycle"]
                data_writer.writerow(header)
            logging.info(f"Created dated CSV file: {dated_file_path}")
        
        # Create or update symlink to point to current dated file
        try:
            # Remove old symlink if it exists
            if os.path.islink(symlink_path):
                os.remove(symlink_path)
            elif os.path.exists(symlink_path):
                # Backup non-symlink file
                backup_path = os.path.join(self.data_folder, 'data_old.csv')
                os.rename(symlink_path, backup_path)
                logging.warning(f"Backed up existing data.csv to data_old.csv")
            
            # Create symlink
            os.symlink(dated_file, symlink_path)
            logging.info(f"Created symlink: {symlink_file} -> {dated_file}")
        except Exception as e:
            logging.error(f"Failed to create symlink: {str(e)}")
            # Fallback: use dated file directly if symlink fails
            return dated_file_path
        
        return symlink_path

    def _start_monitor(self):
        """Start the monitor Dash app as a subprocess"""
        try:
            monitor_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'workers', 'monitor.py'))
            
            # Monitor log file
            monitor_log = os.path.join(self.data_folder, 'data_monitor.log')
            
            # Get repository root for working directory
            repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            
            with open(monitor_log, 'ab') as logf:
                # Start monitor process - pass the data folder path
                proc = subprocess.Popen(
                    [sys.executable, monitor_path, '--input', self.data_folder],
                    stdout=logf,
                    stderr=logf,
                    cwd=repo_root
                )
                
                # Give process time to start
                time.sleep(0.2)
                
                if proc.poll() is None:
                    # Process is running
                    self.monitor_proc = proc
                    self.monitor_started = True
                    
                    # Write status file
                    status_path = os.path.join(self.data_folder, 'data_monitor.proc')
                    try:
                        with open(status_path, 'w') as sf:
                            sf.write(f'started\npid:{proc.pid}\nlog:{monitor_log}\n')
                        logging.info(f"Monitor started with PID {proc.pid}")
                    except Exception as e:
                        logging.warning(f"Could not write monitor status file: {e}")
                else:
                    # Process exited quickly
                    self.monitor_proc = None
                    self.monitor_started = False
                    
                    status_path = os.path.join(self.data_folder, 'data_monitor.proc')
                    try:
                        with open(status_path, 'w') as sf:
                            sf.write(f'failed to start\nreturncode:{proc.returncode}\nlog:{monitor_log}\n')
                        logging.error(f"Monitor failed to start with return code {proc.returncode}")
                    except Exception:
                        pass
                        
        except Exception as e:
            self.monitor_proc = None
            self.monitor_started = False
            logging.error(f"Failed to start monitor: {str(e)}")
            
            # Write error status
            try:
                status_path = os.path.join(self.data_folder, 'data_monitor.proc')
                with open(status_path, 'w') as sf:
                    sf.write(f'exception: {e}\n')
            except Exception:
                pass

    def output(self):
        file = 'data.csv'
        
        list = []
        write_interval = 50  # number of rows before writing to file

        while True:
            try:
                # Check if we need to rotate to a new day
                self._check_and_rotate_day()
                
                # Use timeout to prevent indefinite blocking
                data = self.q_data.get(timeout=5)
                temperature, humidity, temp_0, temp_1, humid_0, humid_1, set_humid, set_temp, duty_cycle = data
                
                # Print to console
                print(f'Temp: {temperature}   Humid: {humidity}  dc: {duty_cycle}  Setpoint: {set_temp, set_humid}')

                time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # Original format: Time, Temperature, Humidity, Temp_0, Temp_1, Humid_0, Humid_1, Set_Temp, Set_Humid, Duty_Cycle
                row = [time_now, temperature, humidity, temp_0, temp_1, humid_0, humid_1, set_temp, set_humid, duty_cycle]

                list.append(row)

                if len(list) >= write_interval:  # write when buffer reaches threshold
                    self._write_to_csv(file, list)
                    list = []
                    
            except Exception as e:
                # Handle queue timeout or other errors
                if len(list) > 0:  # flush remaining data if any
                    logging.warning(f"Queue timeout or error: {str(e)}. Flushing {len(list)} rows.")
                    self._write_to_csv(file, list)
                    list = []
                time.sleep(0.1)
                continue

    def _check_and_rotate_day(self):
        """Check if a new day has started and rotate CSV file if needed"""
        now = datetime.now()
        current_date = now.date()
        
        # Check if we've crossed into a new day
        if current_date != self.current_day:
            logging.info(f"Day boundary crossed: {self.current_day} -> {current_date}")
            
            # Flush any buffered data before rotation
            # (handled in output() exception handler)
            
            # Update tracking variables
            self.current_day = current_date
            self.next_rotation_time = self.time_init + timedelta(days=(current_date - self.time_init.date()).days + 1)
            
            # Create new file and update symlink
            try:
                old_path = self.file_path
                self.file_path = self._create_file()
                logging.info(f"Rotated to new day's CSV: {self.file_path}")
                logging.info(f"Previous day's file: {old_path}")
            except Exception as e:
                logging.error(f"Failed to rotate CSV file: {str(e)}")

    def _write_to_csv(self, filename, rows):
        """Helper method to write rows to CSV file with error handling"""
        try:
            with open(self.file_path, 'a', newline='') as csvfile:
                data_writer = csv.writer(csvfile)
                for r in rows:
                    data_writer.writerow(r)
        except Exception as e:
            logging.error(f"Error writing to CSV file: {str(e)}")
