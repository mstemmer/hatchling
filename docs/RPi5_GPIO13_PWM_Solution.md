# GPIO13 PWM on Raspberry Pi 5 - Configuration Guide

## Quick Answer

**Yes, GPIO13 on RPi 5 can do PWM, but it requires configuration.**

---

## Key Differences

### Raspberry Pi 3/4
- Any GPIO could do software PWM via `RPi.GPIO`
- GPIO13 worked automatically with `GPIO.PWM(13, freq)`
- Less stable but simple

### Raspberry Pi 5 ⚠️
- Only specific GPIO pins have hardware PWM
- GPIO13 CAN do PWM, but needs proper setup
- Must use either:
  1. `RPi.GPIO` (software PWM - slower)
  2. `pigpio` (hardware PWM - better)

---

## Your Current Setup

```python
self.heat = GPIO.PWM(self.heat_pin, 100)  # GPIO13
self.heat.start(0)
self.heat.ChangeDutyCycle(duty_cycle)
```

**On RPi 5**: This MIGHT work but could be:
- ✓ Working fine (lucky!)
- ⚠️ Inconsistent (frequency drifts)
- ✗ Not working at all (no PWM output)

---

## Hardware PWM Pins on RPi 5

| Channel | Pins | Status |
|---------|------|--------|
| PWM0 | GPIO12, GPIO18 | ✓ Primary (recommended) |
| PWM1 | GPIO13, GPIO19 | ⚠️ Secondary (needs config) |

**GPIO12** is the preferred choice!

---

## How to Check Your Setup

Run the diagnostic:
```bash
sudo python3 /home/pi/hatchling/hardware_test_scripts/check_rpi5_pwm.py
```

This will tell you:
- ✓ If GPIO13 PWM works
- ✓ If GPIO12 PWM works (better)
- ✓ If pigpio is available
- ✓ RPi 5 configuration status

---

## Recommended Fix

### Best Option: Switch to GPIO12

**File: `/home/pi/hatchling/settings.yml`**
```yaml
setup_pin:
  data: 17
  latch: 27
  clock: 22
  heat: 12        # ← Changed from 13 (GPIO12 is primary PWM)
  dir: 24
  step: 6
  sleep: 5
  DHT22_sensor: 25
```

**Pros:**
- GPIO12 is the primary PWM0 channel on RPi 5
- Works reliably with RPi.GPIO
- No code changes needed
- Best stability and performance

**Check if GPIO12 conflicts with anything:**
```bash
# Look in your hardware docs
grep -r "GPIO12" /home/pi/hatchling/docs/
grep -r "gpio12" /home/pi/hatchling/
```

---

## Alternative: Keep GPIO13, Use pigpio

If you MUST use GPIO13:

### Step 1: Install pigpio
```bash
sudo apt update
sudo apt install pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Step 2: Update controller.py
```python
import pigpio

# In __init__:
self.pi = pigpio.pi()
self.pwm_pin = 13
self.pwm_freq = 1000  # Hz

# In pid_controller:
duty_percent = self.duty_cycle  # 0-100
pwm_value = int((duty_percent / 100) * 1000000)  # Convert to 0-1000000
self.pi.hardware_PWM(self.pwm_pin, self.pwm_freq, pwm_value)

# On shutdown:
self.pi.hardware_PWM(self.pwm_pin, self.pwm_freq, 0)
self.pi.stop()
```

**Cons:**
- More complex code changes
- Requires pigpio daemon running
- Harder to debug

---

## Decision Tree

```
Do you want the simplest, most reliable solution?
├─ YES → Switch to GPIO12 (edit settings.yml only)
└─ NO → Keep GPIO13
    ├─ Is GPIO.PWM(13) working fine?
    │  ├─ YES → Leave it (risk: may be unstable)
    │  └─ NO → Switch to GPIO12 or use pigpio
    └─ Do you want hardware PWM quality?
       ├─ YES → Use pigpio (install + code changes)
       └─ NO → Switch to GPIO12
```

---

## My Recommendation

**For your Hatchling incubator control:**

1. ✅ **First**: Run the diagnostic
   ```bash
   sudo python3 check_rpi5_pwm.py
   ```

2. ✅ **If GPIO13 works fine**: Keep it as is
   
3. ✅ **If GPIO13 fails**: Change to GPIO12
   - Edit `settings.yml`: `heat: 12`
   - Restart hatchling
   - Done!

4. ✅ **For maximum stability**: Use GPIO12 regardless
   - More reliable hardware PWM support
   - Standard configuration for RPi 5
   - Recommended by Raspberry Pi Foundation

---

## Testing After Fix

```bash
# Run full MDD10 test
sudo python3 /home/pi/hatchling/hardware_test_scripts/test_mdd10_heater.py

# Monitor logs
tail -f /home/pi/hatchling/data/2026-03-08_chicken/hatch.log

# Check duty cycle changes
watch -n 1 'tail -5 /home/pi/hatchling/data/2026-03-08_chicken/data.csv | cut -d, -f10'
```

---

## Summary

| Aspect | GPIO13 | GPIO12 |
|--------|--------|--------|
| RPi 5 Native Support | ⚠️ Secondary | ✓ Primary |
| RPi.GPIO Compatibility | ⚠️ Varies | ✓ Reliable |
| Hardware PWM | ⚠️ Needs Setup | ✓ Native |
| Code Changes | None | Edit settings.yml only |
| Recommended | ❌ No | ✅ YES |

**Recommendation: Use GPIO12** ← Simplest, most reliable
