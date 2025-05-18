import time
from machine import Pin
from sys import stdin
import uselect

csv_filename = "data.csv"
pin = Pin("LED", Pin.OUT)

def save_to_csv(data):
  with open(csv_filename, "a") as f:
    f.write(data + "\n")

for i in range(4):
  pin.toggle()
  time.sleep(1) # sleep 0.5sec
    # blink 4 times

while True:
  select_result = uselect.select([stdin], [], [], 0)
  buffer = ''
  while select_result[0]:
    input_character = stdin.read(1)
    if input_character != ',':
        buffer += input_character
    else:
        save_to_csv(buffer)
        buffer = ''
    select_result = uselect.select([stdin], [], [], 0)