import time
from machine import Pin, PWM
from sys import stdin
import uselect

csv_filename = "debug.txt"
led = Pin("LED", Pin.OUT)

def save_to_csv(data):
  with open(csv_filename, "a") as f:
    f.write(data + "\n")

def set_pwm_percent(pwm, percent):
    value = int(65535 * percent / 100)
    pwm.duty_u16(value)

# check if program is running on Pico
for i in range(4):
  led.toggle()
  time.sleep(1) # sleep 0.5sec
    # blink 4 times

# GPIO25 mit PWM initialisieren (Onboard-LED)
pwm = PWM(Pin(14))
pwm.freq(35000) # Frequenz in Hertz (Hz) einstellen

while True:
    line_in = stdin.readline().strip()
    try:
        # Try to interpret as integer (for PWM percent)
        percent = int(line_in)
        set_pwm_percent(pwm, percent)
        save_to_csv(f"set_pwm:{percent}")
    except ValueError:
        # Not an integer, treat as command string
        if line_in == "led_on":
            led.on()
            save_to_csv(line_in)
        elif line_in == "led_off":
            led.off()
            save_to_csv(line_in)
        else:
            save_to_csv('no_eval')
