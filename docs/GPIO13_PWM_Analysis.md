# GPIO13 PWM Duty Cycle Analysis
# /home/pi/hatchling/brood/workers/controller.py

## ISSUE IDENTIFIED:

### Current Code (Lines 49-50, 86):
```python
GPIO.setup(heat_pin, GPIO.OUT)
GPIO.output(heat_pin, GPIO.HIGH)  # <-- Sets pin HIGH
# ...later...
self.heat = GPIO.PWM(heat_pin, 100)
self.heat.start(0)  # <-- Starts at 0% duty
```

### POTENTIAL PROBLEMS:

1. **Initial GPIO.output() may conflict with PWM**
   - Setting GPIO.output(13, HIGH) puts the pin in a definite state
   - Then starting PWM should override this, but timing might matter
   - Recommend removing the GPIO.output() call before PWM starts

2. **PWM 0% Duty Cycle Behavior**
   - With 0% duty on GPIO13, the pin should be LOW
   - This should mean:
     - MOSFET gate = LOW = MOSFET OFF = Heater OFF ✓
   - But verify with a multimeter that GPIO13 is actually 0V when duty=0%

3. **Missing PWM Stop on Shutdown**
   - Line 227 calls `self.heat.ChangeDutyCycle(0)` but doesn't call `pwm.stop()`
   - Should also call `pwm.stop()` to properly release the PWM

### RECOMMENDED FIXES:

#### Fix 1: Remove conflicting GPIO.output() before PWM
```python
# Line 49-50: REMOVE this line before PWM setup
# GPIO.output(self.heat_pin, GPIO.HIGH)  # DELETE THIS

# Or better: Set LOW as safe default
GPIO.output(self.heat_pin, GPIO.LOW)  # Heater OFF by default
```

#### Fix 2: Properly stop PWM on shutdown (Line 227)
```python
self.heat.stop()  # Add this line
self.heat.ChangeDutyCycle(0)
fan_control(0)
GPIO.output(self.heat_pin, GPIO.LOW)  # Ensure pin is LOW
```

#### Fix 3: Verify PWM is applied correctly
```python
self.heat = GPIO.PWM(self.heat_pin, 100)
self.heat.start(0)
# Verify: Should read 0V on GPIO13 with multimeter
```

### VERIFICATION STEPS:

1. Run the test script: `sudo python3 hardware_test_scripts/test_pwm_duty.py`
2. Use a multimeter to check GPIO13 voltage:
   - At 0% duty: Should read ~0V (LOW)
   - At 50% duty: Should read ~1.65V (oscillating)
   - At 100% duty: Should read ~3.3V (HIGH)
3. If readings are wrong, check:
   - MOSFET circuit connections
   - Pull-up/pull-down resistors
   - GPIO13 pin itself (might be damaged)
