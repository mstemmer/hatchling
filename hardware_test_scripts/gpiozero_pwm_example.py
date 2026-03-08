#!/usr/bin/env python3
"""
Example of using software PWM with gpiozero on Raspberry Pi 5
gpiozero provides an easy-to-use interface for GPIO control with software PWM fallback
"""

from gpiozero import PWMLED
from time import sleep

# Example 1: Basic software PWM on GPIO12
print("Example 1: Basic Software PWM with gpiozero")
print("=" * 50)

# Create a PWM LED on GPIO12 (gpiozero handles software PWM automatically if needed)
heater = PWMLED(12)

# Set to 50% duty cycle
heater.value = 0.5
print(f"GPIO12 set to 50% duty cycle: {heater.value}")
sleep(2)

# Set to 100% (fully on)
heater.value = 1.0
print(f"GPIO12 set to 100% duty cycle: {heater.value}")
sleep(30)

# Set to 0% (off)
heater.value = 0.0
print(f"GPIO12 set to 0% duty cycle: {heater.value}")
sleep(2)

# Example 2: Pulse (fade in/out)
print("\nExample 2: Pulse (Fade In/Out)")
print("=" * 50)
heater.pulse(fade_in_time=2, fade_out_time=2, n=2, background=True)
sleep(8)
heater.off()

# Example 3: Blink
print("\nExample 3: Blink")
print("=" * 50)
heater.blink(on_time=0.5, off_time=0.5, n=4, background=True)
sleep(4)
heater.off()

# Example 4: Hardware PWM (if available on your pin/RPi)
print("\nExample 4: Hardware PWM (RPi5 GPIO12)")
print("=" * 50)
try:
    from gpiozero import PWMLED
    # On RPi5, GPIO12 can use hardware PWM
    heater = PWMLED(12, pin_factory=None)  # Let gpiozero choose the best factory
    heater.value = 0.75
    print(f"GPIO12 set to 75% duty cycle (hardware PWM if available)")
    sleep(2)
    heater.off()
except Exception as e:
    print(f"Error: {e}")

print("\nExample complete!")
