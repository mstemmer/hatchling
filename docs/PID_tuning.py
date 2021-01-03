import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, date, timedelta
import datetime

dc = 25  #25% duty cylce

data = pd.read_csv('2020-11-18_data.csv')
data.columns = ['time', 'temp', 'humid', 'temp_raw', 'humid_raw', 'sensor', 'set_humid', 'set_temp', 'dc']


data[['time']] = pd.to_datetime(data['time'], format='%H:%M:%S') #format time back to datetime readable
dc_start = data[data['dc'] == dc].index[0]
# print(dc_start)
t0 = data.iloc[dc_start]['time'] #start of heating
data[['time_delta']] = data[['time']].subtract(t0) # time difference from heating start onwards
data['seconds'] = data['time_delta'].dt.total_seconds() # same in seconds

print(data)

TD = data['seconds'].iloc[158] - data['seconds'].iloc[142] # get dead time; estimated from table
# TD = TD * 0.25
# TD = 30
print(f"Dead time TD: {TD}s")


T1 = data['temp'].min() # define lowest and highest Temperature in table
T2 = data['temp'].max()
Tdelta = T2 - T1

min = data[data['temp'] == T1].index[0] # get first index of highest and lowest temperature
max = data[data['temp'] == T2].index[0]

tmin = round(data['seconds'].iloc[min]) # get times in seconds from start of T1 & T2
tmax = round(data['seconds'].iloc[max])
tdelta = tmax - tmin

index_tau_3 = data['temp'].sub(round(T1 + (0.283 * Tdelta))).abs().idxmin() #subtract search vlaue from all others, give absolut value and return index with lowest value
index_tau = data['temp'].sub(round(T1 + (0.632 * Tdelta))).abs().idxmin()

tau_3 = data.iloc[index_tau_3]['seconds']
tau = data.iloc[index_tau]['seconds']

tc = (tau - tau_3) *3/2
gain = Tdelta / dc #


print(f"Min Temp (T1): {T1}°C")
print(f"Max Temp (T2): {T2}°C")
print(f"Temp difference: {Tdelta}°C")

print(f'Time at min temp: {tmin}s')
print(f'Time at max temp: {tmax}s')
print(f'Time difference: {tdelta}s')
# print(f'Time at tau/3: {tau_3}s')
# print(f'Time at tau: {tau}s')
print(f'Time constant tau: {tc}s')
print(f'Gain (K): {gain}°C/%')

# Ziegler-Nichols Closed Loop:
Kc = round((1.2 * tc) / (gain * TD),1)
Ti = 2.0 * TD
Td = 0.5 * TD
print(f'Ziegler-Nichols Closed Loop= Kc: {Kc}%/°C; Ti: {Ti}s; Td: {Td}s')

# Cohen-Coon:
Kc = (tc / (gain * TD)) * (TD / (4 * tc) + 4 / 3)
Ti = TD * (32 * tc + 6 * TD) / (13 * tc + 8 * TD)
Td = 4 * TD * tc / (2 * TD + 11 * tc)
print(f'Cohen-Coon= Kc: {Kc}%/°C; Ti: {Ti}s; Td: {Td}s')


# plot = sns.lineplot(x = data['seconds'], y = data['temp'], data=data)
# plt.show()
