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
        while True:

            self.humid, self.temp, self.set_humid, self.set_temp, self.duty_cycle = self.q_data.get()
            print('Values received', self.humid, self.temp, self.set_humid, self.set_temp)
            time_now = datetime.now().time().strftime('%H:%M:%S')
            file = f'{self.data_file}_3'
            row = [time_now, self.temp, self.humid, self.duty_cycle]
            with open(os.path.join(self.data_folder, file), 'a', newline='') as csvfile:
                dhtwriter = csv.writer(csvfile)
                dhtwriter.writerow(row)
                csvfile.close()
