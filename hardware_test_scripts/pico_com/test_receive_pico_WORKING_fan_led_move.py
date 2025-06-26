import time
from machine import Pin, PWM
from sys import stdin
import uselect

csv_filename = "debug.txt"
led = Pin("LED", Pin.OUT)
step_move = Pin(6, Pin.OUT)  # Pin for moving eggs
step_sleep = Pin(5, Pin.OUT)  # Pin for sleep mode
step_sleep.off()
step_move.off()

steps_per_round = 150
step_count = steps_per_round * 32 # a full round in Mode 101
step_delay = 0.0208 / 16  # controls the speed of the motor


def save_to_csv(data):
  with open(csv_filename, "a") as f:
    f.write(data + "\n")

def set_pwm_percent(pwm, percent):
    value = int(65535 * percent / 100)
    pwm.duty_u16(value)

def move_eggs() :
        step_sleep.on()
        time.sleep(0.2) # wakeup time is min. 1 millisecond
        for x in range(step_count):
            step_move.on()
            time.sleep(step_delay)
            step_move.off()
            time.sleep(step_delay)
        time.sleep(0.2)
        step_sleep.off() # put DRV8825 into sleep mode --> draws much less energy


# check if program is running on Pico
for i in range(4):
  led.toggle()
  time.sleep(1) # sleep 0.5sec
    # blink 2 times



# GPIO25 mit PWM initialisieren (Onboard-LED)
pwm = PWM(Pin(14))
pwm.freq(35000) # Frequenz in Hertz (Hz) einstellen


while True:
    line_in = stdin.readline().strip()
    try:
        # Try to interpret as integer (for PWM percent)
        percent = int(line_in)
        set_pwm_percent(pwm, percent)
        save_to_csv(f"set_fan_pwm:{percent}")
    except ValueError:
        # Not an integer, treat as command string
        if line_in == "move_eggs":
            move_eggs()
            save_to_csv(line_in)
        elif line_in == "led_on":
            led.on()
            save_to_csv(line_in)
        elif line_in == "led_off":
            led.off()
            save_to_csv(line_in)
        else:
            save_to_csv('no_eval')
