import pandas as pd
from datetime import datetime
import csv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

headers = ['Day', 'Eggs_moved', 'Time', 'Temp_avg', 'Temp_1', 'Temp_2', 'Humid_avg', 'Humid_1', 'Humid_2']
df = pd.read_csv('/home/pi/brutautomat/data/output_0330_new.csv',names=headers)
print (df)

#df['Time'] = df['Time'].map(lambda x: datetime.strptime(str(x), '%Y/%m/%d %H:%M:%S.%f'))
x = df['Time']
y = df['Temp_avg']

# plot
plt.plot(x,y)
# beautify the x-labels
plt.gcf().autofmt_xdate()

plt.show()
