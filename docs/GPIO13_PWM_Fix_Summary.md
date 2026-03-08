# GPIO13 PWM Duty Cycle Fix - Summary

## Issues Found & Fixed

### Issue 1: GPIO.output() Conflict with PWM
**Problem**: Initial `GPIO.output(13, GPIO.HIGH)` set the pin HIGH before PWM started
- This could interfere with PWM initialization
- Pin should default to LOW (heater OFF) for safety

**Fix**: Changed to `GPIO.output(self.heat_pin, GPIO.LOW)`
- **Location**: Line 50 in controller.py
- **Why**: Ensures heater is OFF during startup

---

### Issue 2: PWM Not Properly Stopped on Shutdown
**Problem**: The shutdown sequence didn't call `pwm.stop()`
- Only changed duty cycle to 0, but didn't release PWM resource
- Could leave pin in undefined state

**Fix**: Added `self.heat.stop()` before `ChangeDutyCycle(0)`
- **Location**: Line 219 in controller.py
- **Sequence**: 
  1. `stop()` - Release PWM control
  2. `ChangeDutyCycle(0)` - Set duty to 0
  3. `GPIO.output(13, LOW)` - Explicitly set pin LOW
  4. `GPIO.cleanup()` - Clean up all GPIO

---

## PWM Duty Cycle Behavior - Expected Results

When duty cycle = **0%**:
- ✓ Pin GPIO13 should output **~0V (LOW)**
- ✓ MOSFET gate = LOW = MOSFET OFF
- ✓ **Heater should be OFF**

When duty cycle = **50%**:
- Pin GPIO13 oscillates between HIGH/LOW
- Multimeter reads ~1.65V average
- MOSFET pulses ON/OFF
- **Heater partially powered**

When duty cycle = **100%**:
- ✓ Pin GPIO13 should output **~3.3V (HIGH)**
- ✓ MOSFET gate = HIGH = MOSFET ON
- ✓ **Heater fully powered**

---

## Verification Steps

### 1. Run the PWM Test Script
```bash
cd /home/pi/hatchling
sudo python3 hardware_test_scripts/test_pwm_duty.py
```

### 2. Measure GPIO13 Voltage
Use a multimeter set to DC voltage:
- **Probe 1**: GPIO13 (pin 33 on RPi GPIO header)
- **Probe 2**: GND (any GND pin on RPi)

Record voltages at each duty cycle:
- [ ] 0% duty: _____ V (should be ~0V)
- [ ] 50% duty: _____ V (should be ~1.65V)
- [ ] 100% duty: _____ V (should be ~3.3V)

### 3. Check Heater Response
Monitor heater behavior in `/home/pi/hatchling/data/[date]_chicken/hatch.log`

Look for:
- Duty cycle decreasing when temp > setpoint
- Duty cycle increasing when temp < setpoint
- Duty cycle staying near 0% when temp at setpoint

---

## Files Modified
- `/home/pi/hatchling/brood/workers/controller.py`
  - Line 50: Changed initial GPIO state from HIGH to LOW
  - Line 219: Added `self.heat.stop()` on shutdown

## Files Created
- `/home/pi/hatchling/hardware_test_scripts/test_pwm_duty.py` - Verification test
- `/home/pi/hatchling/docs/GPIO13_PWM_Analysis.md` - Technical analysis
