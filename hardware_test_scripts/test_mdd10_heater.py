#!/usr/bin/env python3
"""
Test MDD10 motor driver - Both GPIO13 (PWM) and GPIO24 (DIR)
Run with: sudo python3 test_mdd10_heater.py
"""

from RPi import GPIO
import time
import sys

# Setup
GPIO.setmode(GPIO.BCM)
heat_pin = 13  # PWM2
dir_pin = 24   # DIR2

try:
    print("=" * 60)
    print("MDD10 Motor Driver Test - Heater Control")
    print("=" * 60)
    print(f"\nPins Used:")
    print(f"  GPIO{heat_pin} (PWM2) - Speed control")
    print(f"  GPIO{dir_pin} (DIR2) - Direction/Enable control\n")
    
    # Setup pins
    GPIO.setup(heat_pin, GPIO.OUT)
    GPIO.setup(dir_pin, GPIO.OUT)
    print(f"✓ GPIO{heat_pin} setup as OUTPUT (PWM)")
    print(f"✓ GPIO{dir_pin} setup as OUTPUT (Direction)\n")
    
    # Set safe defaults
    GPIO.output(heat_pin, GPIO.LOW)
    GPIO.output(dir_pin, GPIO.LOW)
    print(f"✓ Set GPIO{heat_pin} = LOW (PWM off)")
    print(f"✓ Set GPIO{dir_pin} = LOW (Motor disabled)\n")
    
    time.sleep(1)
    
    # Start PWM
    pwm = GPIO.PWM(heat_pin, 100)  # 100 Hz
    pwm.start(0)
    print(f"✓ PWM started at 0% duty cycle")
    print(f"  Motor should stay OFF (no DIR signal yet)\n")
    
    time.sleep(1)
    
    # Enable motor by setting DIR pin HIGH
    GPIO.output(dir_pin, GPIO.HIGH)
    print(f"✓ GPIO{dir_pin} set to HIGH (Motor enabled/forward)\n")
    
    # Test 0% duty
    print("--- Test 1: 0% Duty Cycle (Motor OFF) ---")
    pwm.ChangeDutyCycle(0)
    print(f"✓ PWM set to 0%")
    print(f"  Expected: Heater OFF, no sound, no heat")
    print(f"  Measure GPIO{heat_pin}: should read ~0V\n")
    time.sleep(2)
    
    # Test 25% duty
    print("--- Test 2: 25% Duty Cycle (Low Power) ---")
    pwm.ChangeDutyCycle(25)
    print(f"✓ PWM set to 25%")
    print(f"  Expected: Heater ON softly, warm")
    print(f"  Measure GPIO{heat_pin}: should read ~0.8V\n")
    time.sleep(2)
    
    # Test 50% duty
    print("--- Test 3: 50% Duty Cycle (Medium Power) ---")
    pwm.ChangeDutyCycle(50)
    print(f"✓ PWM set to 50%")
    print(f"  Expected: Heater ON at medium, noticeable heat")
    print(f"  Measure GPIO{heat_pin}: should read ~1.65V\n")
    time.sleep(2)
    
    # Test 75% duty
    print("--- Test 4: 75% Duty Cycle (High Power) ---")
    pwm.ChangeDutyCycle(75)
    print(f"✓ PWM set to 75%")
    print(f"  Expected: Heater ON strong, hot")
    print(f"  Measure GPIO{heat_pin}: should read ~2.48V\n")
    time.sleep(2)
    
    # Test 100% duty
    print("--- Test 5: 100% Duty Cycle (Full Power) ---")
    pwm.ChangeDutyCycle(100)
    print(f"✓ PWM set to 100%")
    print(f"  Expected: Heater FULL ON, very hot")
    print(f"  Measure GPIO{heat_pin}: should read ~3.3V\n")
    time.sleep(2)
    
    # Disable motor
    print("--- Test 6: Motor Disable (DIR = LOW) ---")
    GPIO.output(dir_pin, GPIO.LOW)
    print(f"✓ GPIO{dir_pin} set to LOW (Motor disabled)")
    print(f"  Expected: Heater OFF regardless of PWM")
    print(f"  PWM still at 100% but motor disabled\n")
    time.sleep(1)
    
    # Back to normal
    pwm.ChangeDutyCycle(0)
    
    print("=" * 60)
    print("TEST COMPLETE - Press Ctrl+C to cleanup")
    print("=" * 60)
    print("\nSummary of what should happen:")
    print("  ✓ When DIR=HIGH: PWM controls heater speed")
    print("  ✓ When DIR=LOW: Heater OFF (safety disable)")
    print("  ✓ GPIO13 voltage changes with PWM duty cycle")
    print("  ✓ GPIO24 controls whether motor responds\n")
    
    while True:
        time.sleep(0.1)
    
except KeyboardInterrupt:
    print("\n\n✓ Cleaning up...")
    pwm.stop()
    GPIO.output(heat_pin, GPIO.LOW)
    GPIO.output(dir_pin, GPIO.LOW)
    GPIO.cleanup()
    print("✓ GPIO cleanup complete")
    sys.exit(0)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    GPIO.cleanup()
    sys.exit(1)
