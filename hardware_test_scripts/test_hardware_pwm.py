#!/usr/bin/env python3
"""
Hardware PWM test for GPIO12 on Raspberry Pi 5
Uses rpi_hardware_pwm (writes to /sys/class/pwm/ sysfs interface)
chip=0, channel=0 → GPIO12
chip=0, channel=1 → GPIO13
"""

from rpi_hardware_pwm import HardwarePWM
from time import sleep

CHIP = 0
CHANNEL = 0  # GPIO12
HZ = 100

print("Hardware PWM Test - GPIO12")
print(f"chip={CHIP}, channel={CHANNEL}, hz={HZ}")
print("=" * 50)

heater = HardwarePWM(pwm_channel=CHANNEL, hz=HZ, chip=CHIP)
heater.start(0)

print("\n1. 0% duty cycle (OFF)...")
heater.change_duty_cycle(0)
sleep(3)

print("2. 25% duty cycle...")
heater.change_duty_cycle(25)
sleep(3)

print("3. 50% duty cycle...")
heater.change_duty_cycle(50)
sleep(3)

print("4. 75% duty cycle...")
heater.change_duty_cycle(75)
sleep(3)

print("5. 100% duty cycle (FULL ON)...")
heater.change_duty_cycle(100)
sleep(3)

print("6. Back to 0% (OFF)...")
heater.change_duty_cycle(0)
sleep(1)

heater.stop()
print("\nTest complete!")
