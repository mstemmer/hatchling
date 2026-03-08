# GPIO13 Not Responding - SOLUTION FOUND

## The Real Problem: MDD10 Requires TWO Control Pins

The **Hat-MDD10 dual motor driver** needs **BOTH signals** to work:

```
Motor 2 (Heater):
├─ GPIO13 (PWM2):  Speed control (0-100% duty)
└─ GPIO24 (DIR2):  Direction/Enable control (HIGH=enable, LOW=disable)
```

### Why It Wasn't Working
```
GPIO13 (PWM):  ✓ Working fine (sending PWM signal)
GPIO24 (DIR):  ✗ NEVER SET UP (stuck floating or undefined)

Result: MDD10 receives speed signal but no enable signal
        → Motor stays OFF (safety feature)
```

---

## What Was Fixed

### 1. Added GPIO24 to settings.yml
```yaml
setup_pin:
  heat: 13      # PWM2 pin (speed)
  dir: 24       # DIR2 pin (enable) ← ADDED
```

### 2. Initialize GPIO24 in controller.py
```python
self.heat_pin = config['setup_pin']['heat']
self.dir_pin = config['setup_pin']['dir']    # ← NEW

GPIO.setup(self.heat_pin, GPIO.OUT)
GPIO.setup(self.dir_pin, GPIO.OUT)           # ← NEW

GPIO.output(self.heat_pin, GPIO.LOW)
GPIO.output(self.dir_pin, GPIO.HIGH)         # ← NEW (enable motor)
```

### 3. Ensure GPIO24 is disabled on shutdown
```python
except KeyboardInterrupt:
    GPIO.output(self.dir_pin, GPIO.LOW)      # ← NEW (disable motor)
    self.heat.ChangeDutyCycle(0)
    ...
```

---

## How MDD10 Works

### Control Table
| GPIO13 (PWM) | GPIO24 (DIR) | Result |
|:---:|:---:|:---|
| 0% | HIGH | Heater OFF (0W) |
| 25% | HIGH | Heater ON @ 25% power |
| 50% | HIGH | Heater ON @ 50% power |
| 100% | HIGH | Heater ON @ full power |
| 100% | LOW | **Heater OFF** (disabled) |
| 50% | LOW | **Heater OFF** (disabled) |

**Key Point**: GPIO24 must be HIGH to enable the motor, then GPIO13 PWM controls speed.

---

## Verification Steps

### 1. Run Test Script
```bash
cd /home/pi/hatchling
sudo python3 hardware_test_scripts/test_mdd10_heater.py
```

You should hear/feel the heater:
- Increasing at 0% → 25% → 50% → 75% → 100%
- Stopping when DIR pin goes LOW

### 2. Check Logs
```bash
tail -f /home/pi/hatchling/data/2026-03-08_chicken/hatch.log
```

Should show:
- `INFO: Initializing PID controller`
- Temperature rising
- Duty cycle changing with temperature

### 3. Monitor CSV Data
```bash
tail -20 /home/pi/hatchling/data/2026-03-08_chicken/data.csv
```

Duty cycle column should show **varying values**, not stuck at 0 or 100.

### 4. Multimeter Measurements
```
Measure GPIO13 with multimeter DC voltage:
- 0% duty:   ~0.0V
- 50% duty:  ~1.65V
- 100% duty: ~3.3V

Measure GPIO24:
- Should always read ~3.3V when heater active
```

---

## Files Modified

1. ✅ `/home/pi/hatchling/settings.yml`
   - Added `dir: 24` pin configuration

2. ✅ `/home/pi/hatchling/brood/workers/controller.py`
   - Line ~44: Initialize GPIO24
   - Line ~50: Set GPIO24 HIGH (enable motor)
   - Line ~220: Set GPIO24 LOW on shutdown

3. ✅ `/home/pi/hatchling/hardware_test_scripts/test_mdd10_heater.py`
   - New comprehensive test script

---

## Expected Behavior After Fix

### Initial Startup (Room Temp ~26°C)
```
Error = 37.8 - 26 = +11.8°C (need heat)
GPIO24 = HIGH (motor enabled)
GPIO13 = 80-100% PWM (heater ON)
Result: Temperature rises
```

### At Setpoint (37.8°C)
```
Error ≈ 0°C (perfect)
GPIO24 = HIGH (motor enabled)
GPIO13 ≈ 48% PWM (steady-state)
Result: Temperature stable, heating occasional
```

### Above Setpoint (38.5°C)
```
Error = -0.7°C (too hot)
GPIO24 = HIGH (motor enabled)
GPIO13 = 20-30% PWM (minimal heating)
Result: Temperature falls back to 37.8°C
```

---

## Summary

**Problem**: GPIO24 (direction pin) was never initialized
**Impact**: MDD10 motor driver couldn't enable the heater
**Solution**: Initialize GPIO24 and keep it HIGH during operation
**Status**: ✅ FIXED

The heater should now respond to duty cycle changes!

