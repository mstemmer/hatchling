import time
from datetime import datetime
import csv
import os
import pandas as pd
import logging
# import brood.workers.test_dash as testdash


class Output():

    def __init__(self, config, q_data, time_init):
        self.data_folder = config["data_folder"]
        self.data_file = config["data_file"]
        self.config = config
        self.time_init = time_init
        # print(self.data_folder)
        self.q_data = q_data
        self.output()

    def output(self):
        file = f'{str(self.time_init.date())}_{self.data_file}.csv'
        file_path = os.path.join(self.data_folder, file)

        list = []

        while True:

            humid, temp, humid_raw, temp_raw, sens, \
            set_humid, set_temp, duty_cycle = self.q_data.get()
            # print('Values received', humid, temp, set_humid, set_temp, duty_cycle)
            print(f'Temp: {temp}   Humid: {humid}  dc: {duty_cycle}  Setpoint: {set_temp, set_humid}')

            time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [time_now, humid, temp, humid_raw, temp_raw, sens,
            set_humid, set_temp, duty_cycle]

            list.append(row)

            if len(list) == 1:

                with open(os.path.join(self.data_folder, file), 'a', newline='') as csvfile:
                    data_writer = csv.writer(csvfile)
                    for r in list:

                        data_writer.writerow(r)
                    csvfile.close()
                list = []
