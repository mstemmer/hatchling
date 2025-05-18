import time
from machine import Pin
from sys import stdin
import uselect

csv_filename = "data.csv"
led = Pin("LED", Pin.OUT)

def save_to_csv(data):
  with open(csv_filename, "a") as f:
    f.write(data + "\n")

for i in range(4):
  led.toggle()
  time.sleep(1) # sleep 0.5sec
    # blink 4 times

# while True:
#   select_result = uselect.select([stdin], [], [], 0)
#   buffer = ''
#   while select_result[0]:
#     line_in = stdin.readline()
#     save_to_csv(line_in)


while True:
  line_in = stdin.readline().strip()
  if line_in == "led_on":
      led.on()
      save_to_csv(line_in)
  elif line_in == "led_off":
      led.off()
      save_to_csv(line_in)
  else:
      save_to_csv('no_eval')
