import time
from datetime import datetime
import pandas as pd
import csv
import os

class Output():

    def __init__(self, config, q_data):
        self.data_folder = config["data_folder"]
        self.data_file = config["data_file"]
        self.config = config
        # print(self.data_folder)
        self.q_data = q_data
        self.output()

    def output(self):
        file = f'{str(datetime.now().date())}_{self.data_file}.csv'
        file_path = os.path.join(self.data_folder, file)
        if os.path.exists(file_path) and self.config["resume"] == True: # delete data file if init == True
            os.remove(file_path)

        list = []

        while True:

            self.humid, self.temp, self.humid_raw, self.temp_raw, sens, \
            self.set_humid, self.set_temp, self.duty_cycle = self.q_data.get()
            # print('Values received', self.humid, self.temp, self.set_humid, self.set_temp, self.duty_cycle)
            print(f'Temp: {self.temp}   Humid: {self.humid}  dc: {self.duty_cycle}  Setpoint: {self.set_temp, self.set_humid}')

            time_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            row = [time_now, self.humid, self.temp, self.humid_raw, self.temp_raw, sens,
            self.set_humid, self.set_temp, self.duty_cycle]

            list.append(row)

            if len(list) == 1:

                with open(os.path.join(self.data_folder, file), 'a', newline='') as csvfile:
                    data_writer = csv.writer(csvfile)
                    for r in list:

                        data_writer.writerow(r)
                    csvfile.close()
                list = []
