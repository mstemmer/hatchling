import time
from datetime import datetime
import csv
import os
import pandas as pd
import logging
# import brood.workers.test_dash as testdash


class Output():

    def __init__(self, config, q_data, time_init, data_folder):
        self.data_folder = data_folder
        self.config = config
        self.time_init = time_init
        self.q_data = q_data
        self.output()

    def output(self):
        file = 'data.csv'
        file_path = os.path.join(self.data_folder, file)

        list = []
        write_interval = 50  # number of rows before writing to file

        while True:
            try:
                # Use timeout to prevent indefinite blocking
                data = self.q_data.get(timeout=5)
                temperature, humidity, temp_0, temp_1, humid_0, humid_1, set_humid, set_temp, duty_cycle = data
                
                print(f'Temp: {temperature}   Humid: {humidity}  dc: {duty_cycle}  Setpoint: {set_temp, set_humid}')

                time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

    def _write_to_csv(self, filename, rows):
        """Helper method to write rows to CSV file with error handling"""
        try:
            with open(os.path.join(self.data_folder, filename), 'a', newline='') as csvfile:
                data_writer = csv.writer(csvfile)
                for r in rows:
                    data_writer.writerow(r)
        except Exception as e:
            logging.error(f"Error writing to CSV file: {str(e)}")
