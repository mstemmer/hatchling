#!/usr/bin/env python3
"""
Test script to verify GPIO13 PWM behavior for heater control
Run with: sudo python3 test_pwm_duty.py
"""

from RPi import GPIO
import time
import sys

# Setup
GPIO.setmode(GPIO.BCM)
heat_pin = 13

try:
    print("=" * 60)
    print("GPIO13 PWM Duty Cycle Test")
    print("=" * 60)
    
    # Setup pin
    GPIO.setup(heat_pin, GPIO.OUT)
    print(f"\n✓ GPIO{heat_pin} setup as OUTPUT")
    
    # Initial state
    GPIO.output(heat_pin, GPIO.HIGH)
    print(f"✓ GPIO{heat_pin} set to HIGH")
    time.sleep(0.5)
    
    # Start PWM
    pwm = GPIO.PWM(heat_pin, 100)  # 100 Hz frequency
    pwm.start(0)
    print(f"\n✓ PWM started at 0% duty cycle")
    print(f"  Expected: Pin LOW (heater OFF)")
    print(f"  Measure voltage on GPIO{heat_pin} with multimeter")
    print(f"  Should read: ~0V (LOW)")
    
    time.sleep(2)
    
    # Test 50% duty
    pwm.ChangeDutyCycle(50)
    print(f"\n✓ PWM changed to 50% duty cycle")
    print(f"  Expected: Pin alternates HIGH/LOW")
    print(f"  Measure voltage on GPIO{heat_pin} with multimeter")
    print(f"  Should read: ~1.65V (oscillating)")
    
    time.sleep(2)
    
    # Test 100% duty
    pwm.ChangeDutyCycle(100)
    print(f"\n✓ PWM changed to 100% duty cycle")
    print(f"  Expected: Pin HIGH (heater FULL ON)")
    print(f"  Measure voltage on GPIO{heat_pin} with multimeter")
    print(f"  Should read: ~3.3V (HIGH)")
    
    time.sleep(2)
    
    # Back to 0%
    pwm.ChangeDutyCycle(0)
    print(f"\n✓ PWM changed back to 0% duty cycle")
    print(f"  Expected: Pin LOW (heater OFF)")
    print(f"  Measure voltage on GPIO{heat_pin} with multimeter")
    print(f"  Should read: ~0V (LOW)")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE - Press Ctrl+C to exit")
    print("=" * 60)
    
    while True:
        time.sleep(0.1)
    
except KeyboardInterrupt:
    print("\n\n✓ Cleaning up...")
    pwm.stop()
    GPIO.cleanup()
    print("✓ GPIO cleanup complete")
    sys.exit(0)

except Exception as e:
    print(f"\n✗ Error: {e}")
    GPIO.cleanup()
    sys.exit(1)
