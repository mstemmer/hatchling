import time
from datetime import datetime
import csv
import os

class Output():

    def __init__(self, config, q_data):
        self.data_folder = config["data_folder"]
        self.data_file = config["data_file"]
        print(self.data_folder)
        self.q_data = q_data
        self.output()

    def output(self):
        file = f'{str(datetime.now().date())}_{self.data_file}'
        while True:

            self.humid, self.temp, self.humid_raw, self.temp_raw, sens, \
            self.set_humid, self.set_temp, self.duty_cycle = self.q_data.get()
            print('Values received', self.humid, self.temp, self.set_humid, self.set_temp, self.duty_cycle)
            time_now = datetime.now().time().strftime('%H:%M:%S')
            row = [time_now, self.temp, self.humid, self.temp_raw, self.humid_raw, sens,
            self.set_humid, self.set_temp, self.duty_cycle]
            with open(os.path.join(self.data_folder, file), 'a', newline='') as csvfile:
                dhtwriter = csv.writer(csvfile)
                dhtwriter.writerow(row)
                csvfile.close()
