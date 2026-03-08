#!/usr/bin/env python3
"""
Raspberry Pi 5 GPIO13 PWM Compatibility Check
Run with: sudo python3 check_rpi5_pwm.py
"""

import os
import sys
import subprocess

def run_cmd(cmd):
    """Run command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 70)
    print("Raspberry Pi 5 GPIO13 PWM Compatibility Check")
    print("=" * 70)
    
    # 1. Check RPi Model
    print("\n[1] Checking Raspberry Pi Model...")
    model = run_cmd("cat /proc/device-tree/model")
    print(f"    Model: {model}")
    
    if "Raspberry Pi 5" not in model:
        print("    ⚠️  WARNING: This is not an RPi 5!")
        print("    These checks may not apply to your device.")
    
    # 2. Check Python version
    print("\n[2] Checking Python Version...")
    py_version = run_cmd("python3 --version")
    print(f"    {py_version}")
    
    # 3. Check available PWM chips
    print("\n[3] Checking PWM Chip Configuration...")
    pwm_info = run_cmd("ls -la /sys/class/pwm/")
    if "pwmchip" in pwm_info:
        print("    ✓ PWM chips found:")
        for line in pwm_info.split('\n'):
            if "pwmchip" in line:
                print(f"      {line}")
    else:
        print("    ✗ No PWM chips found!")
    
    # 4. Check GPIO library
    print("\n[4] Checking GPIO Libraries...")
    
    # Check RPi.GPIO
    try:
        import RPi.GPIO as GPIO
        print("    ✓ RPi.GPIO is installed")
    except ImportError:
        print("    ✗ RPi.GPIO NOT installed")
    
    # Check pigpio
    try:
        import pigpio
        print("    ✓ pigpio is installed")
    except ImportError:
        print("    ✗ pigpio NOT installed")
    
    # Check gpiozero
    try:
        import gpiozero
        print("    ✓ gpiozero is installed")
    except ImportError:
        print("    ✗ gpiozero NOT installed")
    
    # 5. Check GPIO13 pinctrl status
    print("\n[5] Checking GPIO13 Pin Configuration...")
    gpio_config = run_cmd("pinctrl get 13")
    if gpio_config:
        print(f"    GPIO13 config: {gpio_config}")
    
    # 6. Check device tree for PWM overlays
    print("\n[6] Checking Device Tree Configuration...")
    cmdline = run_cmd("cat /boot/firmware/cmdline.txt 2>/dev/null || cat /boot/cmdline.txt 2>/dev/null")
    if cmdline:
        if "pwm" in cmdline.lower():
            print("    ✓ PWM found in device tree:")
            print(f"      {cmdline[:80]}...")
        else:
            print("    ℹ️  No explicit PWM configuration in cmdline")
    
    # 7. Test GPIO13 PWM with RPi.GPIO
    print("\n[7] Testing GPIO13 PWM with RPi.GPIO...")
    try:
        import RPi.GPIO as GPIO
        import time
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(13, GPIO.OUT)
        
        print("    Attempting to create PWM on GPIO13...")
        pwm = GPIO.PWM(13, 100)
        pwm.start(0)
        print("    ✓ PWM object created successfully")
        
        # Test duty cycle changes
        pwm.ChangeDutyCycle(50)
        print("    ✓ ChangeDutyCycle(50) - Success")
        
        pwm.ChangeDutyCycle(0)
        print("    ✓ ChangeDutyCycle(0) - Success")
        
        pwm.stop()
        GPIO.cleanup()
        print("    ✓ GPIO13 PWM works with RPi.GPIO!")
        
    except Exception as e:
        print(f"    ✗ GPIO13 PWM FAILED with RPi.GPIO: {e}")
    
    # 8. Test GPIO13 PWM with pigpio
    print("\n[8] Testing GPIO13 PWM with pigpio...")
    try:
        import pigpio
        
        pi = pigpio.pi()
        if not pi.connected:
            print("    ✗ pigpio daemon not running!")
            print("      Run: sudo pigpiod")
        else:
            print("    Attempting hardware PWM on GPIO13...")
            pi.hardware_PWM(13, 1000, 500000)  # 50% duty at 1kHz
            print("    ✓ Hardware PWM set successfully")
            
            pi.hardware_PWM(13, 1000, 0)
            print("    ✓ PWM disabled successfully")
            
            pi.stop()
            print("    ✓ GPIO13 PWM works with pigpio!")
            
    except Exception as e:
        print(f"    ✗ GPIO13 PWM FAILED with pigpio: {e}")
    
    # 9. Test alternative GPIO12 (primary PWM channel)
    print("\n[9] Testing GPIO12 PWM (Primary PWM0 Channel)...")
    try:
        import RPi.GPIO as GPIO
        import time
        
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(12, GPIO.OUT)
        
        print("    Attempting to create PWM on GPIO12...")
        pwm = GPIO.PWM(12, 100)
        pwm.start(0)
        print("    ✓ PWM object created successfully")
        
        pwm.ChangeDutyCycle(50)
        print("    ✓ GPIO12 PWM works (better choice for RPi5)!")
        
        pwm.stop()
        GPIO.cleanup()
        
    except Exception as e:
        print(f"    ✗ GPIO12 PWM FAILED: {e}")
    
    # 10. Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS:")
    print("=" * 70)
    print("""
Based on Raspberry Pi 5 hardware:

✓ OPTION 1 (Recommended): Use GPIO12
  - Primary PWM0 channel
  - Most reliable on RPi 5
  - No additional configuration needed
  - Edit settings.yml: heat: 12

✓ OPTION 2: Use GPIO13 with pigpio
  - GPIO13 can do hardware PWM
  - Requires pigpio daemon
  - More complex but also works
  - Install: sudo apt install pigpio

✓ OPTION 3: Keep GPIO13 with RPi.GPIO
  - If current code works, no change needed
  - Less reliable but simpler
  - Monitor for PWM instability
""")
    
    print("=" * 70)

if __name__ == "__main__":
    main()
