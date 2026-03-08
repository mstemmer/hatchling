# Raspberry Pi 5 GPIO13 PWM Configuration

## Short Answer: YES, but it's more complex on RPi 5

### GPIO13 PWM Capability on Different RPi Models

| Model | GPIO13 PWM | Method | Notes |
|-------|-----------|--------|-------|
| RPi 3/4 | ✓ Yes | `GPIO.PWM()` | Software PWM via RPi.GPIO |
| RPi 5 | ⚠️ Yes, BUT | Hardware PWM | Requires `pigpio` or device tree config |

---

## The Problem with Raspberry Pi 5

### What Changed in RPi 5
- **RPi 3/4**: Used software PWM (any GPIO could generate PWM via `RPi.GPIO`)
- **RPi 5**: Only specific GPIO pins have **hardware PWM** capability
- GPIO13 is NOT a default hardware PWM pin on RPi 5

### Hardware PWM Pins on Raspberry Pi 5
| PWM Channel | GPIO Pins |
|------------|-----------|
| PWM0 | GPIO12, GPIO18 |
| PWM1 | GPIO13, GPIO19 |

**GPIO13 CAN do PWM**, but it requires proper configuration!

---

## The Issue with Current Code

```python
self.heat = GPIO.PWM(self.heat_pin, 100)  # GPIO13
self.heat.start(0)
```

On **Raspberry Pi 5**, this might:
1. ✓ Work with `RPi.GPIO` (uses software PWM - slower, less stable)
2. ✗ Fail silently (no PWM output at all)
3. ⚠️ Work inconsistently (frequency varies)

**Why**: RPi.GPIO on RPi 5 tries to use hardware PWM but GPIO13 might not be properly configured in the device tree.

---

## Solutions

### Option 1: Use `pigpio` (RECOMMENDED for RPi 5)
```python
import pigpio

pi = pigpio.pi()
PWM_PIN = 13
FREQUENCY = 1000  # Hz

# Set PWM to 50%
pi.hardware_PWM(PWM_PIN, FREQUENCY, 500000)  # 500000 = 50% duty (0-1000000)

# Set to 0%
pi.hardware_PWM(PWM_PIN, FREQUENCY, 0)

# Clean up
pi.stop()
```

**Pros:**
- True hardware PWM on RPi 5
- More stable frequency
- Better performance

**Cons:**
- Requires `pigpio` library
- Different API than RPi.GPIO

---

### Option 2: Use Alternative GPIO Pins
```python
# Use GPIO12 instead (better hardware PWM support on RPi 5)
self.heat_pin = 12  # GPIO12 has dedicated PWM0
self.heat = GPIO.PWM(self.heat_pin, 100)
```

**Update settings.yml:**
```yaml
setup_pin:
  heat: 12  # Changed from 13
  dir: 24
```

**Pros:**
- Works reliably with RPi.GPIO
- No library changes needed

**Cons:**
- Need to change pin (might conflict with other hardware)

---

### Option 3: Verify RPi 5 Device Tree Configuration

Check if GPIO13 PWM is enabled:
```bash
# List PWM channels
cat /sys/class/pwm/pwmchip0/npwm

# Check GPIO13 pinctrl
pinctrl get 13

# Check device tree overlay
cat /boot/firmware/cmdline.txt
```

---

## What You Should Do

### Step 1: Test Current Setup
```bash
sudo python3 /home/pi/hatchling/hardware_test_scripts/test_mdd10_heater.py
```

**If it works:** ✓ Leave as is (GPIO.PWM is working fine)
**If it doesn't:** ⚠️ Try one of the fixes below

### Step 2: Quick Diagnosis Test
```bash
# Check which RPi you have
cat /proc/device-tree/model

# Test GPIO13 directly with pigpio
python3 -c "import pigpio; pi=pigpio.pi(); pi.hardware_PWM(13, 1000, 500000); print('PWM set'); import time; time.sleep(2); pi.stop()"
```

### Step 3: Choose Fix Based on Test Results

**If pigpio test works but GPIO.PWM doesn't:**
→ Use Option 1 (switch to `pigpio`)

**If GPIO.PWM works:**
→ No change needed

**If neither works:**
→ Use Option 2 (switch to GPIO12)

---

## Recommended Fix for Your Setup

Given your current code structure, here's the **minimal change**:

**File: `/home/pi/hatchling/settings.yml`**
```yaml
setup_pin:
  heat: 12      # Changed from 13 (GPIO12 has better PWM support)
  dir: 24
```

**Why**: GPIO12 is the primary PWM0 channel on RPi 5, guaranteed to work with `RPi.GPIO`.

---

## Testing Commands

```bash
# Check your RPi model
uname -m && cat /proc/device-tree/model

# Test GPIO13 voltage with current code
gpio readall | grep GPIO13

# Monitor PWM on GPIO13
sudo apt install wiringpi
gpio pwm 12 500  # PWM on GPIO12 (if available)

# Use multimeter to measure GPIO13 during test
tail -f /home/pi/hatchling/data/2026-03-08_chicken/hatch.log
```

---

## Summary

| Scenario | Solution |
|----------|----------|
| GPIO13 PWM works fine | ✓ No change needed |
| GPIO13 PWM not working | Use GPIO12 or switch to `pigpio` |
| Want maximum reliability | Switch to GPIO12 (primary PWM channel) |

Would you like me to implement any of these fixes?
