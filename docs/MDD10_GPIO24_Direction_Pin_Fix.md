# MDD10 Dual Motor Driver - GPIO13 Not Responding - ROOT CAUSE

## The Real Problem

The **Hat-MDD10** is a dual motor driver that requires **TWO control signals per motor**:

```
Motor 2 (Heater):
├── PWM2 (GPIO13) ← Speed/Duty Cycle control
└── DIR2 (GPIO24) ← Direction control (MUST BE SET!)
```

### Current Code
```python
self.heat = GPIO.PWM(self.heat_pin, 100)  # GPIO13 PWM only
self.heat.start(0)
self.heat.ChangeDutyCycle(duty)  # Changes PWM, but...
```

### Missing Code
```python
# GPIO24 (DIR2) is NEVER initialized or set!
# Without it, the MDD10 motor driver has no "enable" signal
# PWM signal alone cannot activate the motor
```

---

## MDD10 Control Requirements

### Input Signals
| Signal | Pin | Function |
|--------|-----|----------|
| PWM1 | GPIO12 | Motor 1 speed (0-100%) |
| DIR1 | GPIO26 | Motor 1 direction (0=fwd, 1=rev) |
| PWM2 | GPIO13 | Motor 2 speed (0-100%) ← **HEATER** |
| DIR2 | GPIO24 | Motor 2 direction (0=fwd, 1=rev) ← **MISSING** |

### Motor Behavior
- **Without DIR signal**: Motor disabled, no response to PWM
- **With DIR=0 + PWM**: Motor forward at speed
- **With DIR=1 + PWM**: Motor reverse at speed

---

## Why PWM Alone Doesn't Work

```
Scenario: GPIO13 = PWM at 50%, GPIO24 = Not Set (floating)
├─ MDD10 receives PWM signal
├─ MDD10 looks for DIR signal
├─ DIR signal is undefined (floating)
└─ Motor stays OFF (safety feature)

Scenario: GPIO13 = PWM at 50%, GPIO24 = HIGH (direction set)
├─ MDD10 receives PWM signal
├─ MDD10 receives valid DIR signal
├─ Motor activates and runs at 50% speed ✓
```

---

## The Fix Required

### 1. Initialize GPIO24 (DIR2) Pin
```python
# In BroodController.__init__()
self.dir_pin = config['setup_pin']['dir']  # Add 'dir' to settings.yml

GPIO.setup(self.heat_pin, GPIO.OUT)   # PWM pin
GPIO.setup(self.dir_pin, GPIO.OUT)    # Direction pin (MISSING!)

GPIO.output(self.heat_pin, GPIO.LOW)  # Safe default
GPIO.output(self.dir_pin, GPIO.HIGH)  # Set direction for forward (heating)
```

### 2. Ensure GPIO24 is Set Before Using PWM
```python
# In pid_controller()
def pid_controller(self, curr_value):
    if 'fixed_dc' in self.config:
        self.duty_cycle = self.config["fixed_dc"]
    else:
        self.duty_cycle = self.pid(curr_value)
    
    # IMPORTANT: Set direction before changing PWM
    GPIO.output(self.dir_pin, GPIO.HIGH)  # Enable motor forward
    self.heat.ChangeDutyCycle(self.duty_cycle)
```

### 3. Update settings.yml
```yaml
setup_pin:
  data: 17
  latch: 27
  clock: 22
  heat: 13        # PWM2 pin
  dir: 24         # DIR2 pin (ADD THIS!)
  step: 6
  sleep: 5
  DHT22_sensor: 25
```

---

## Verification Checklist

After implementing the fix:

1. **Check settings.yml** has `dir: 24` entry
2. **Check controller.py** initializes GPIO24
3. **Check controller.py** sets GPIO24 HIGH before PWM changes
4. **Monitor GPIO pins**:
   ```bash
   # GPIO13 should show voltage changes
   # GPIO24 should stay HIGH (always enabled)
   ```
5. **Test heating**:
   - Temperature should rise
   - Duty cycle should change with temperature
   - Heater should respond smoothly

---

## Complete MDD10 Heater Control Circuit

```
Raspberry Pi
├─ GPIO13 (PWM2) ──┬─→ MDD10 PWM2 input
├─ GPIO24 (DIR2) ──┼─→ MDD10 DIR2 input
└─ GND ────────────┘
                  
MDD10 Module
├─ Motor OUT1 ─→ Heater Coil +
└─ Motor OUT2 ─→ Heater Coil -

When GPIO13 = 0%, GPIO24 = HIGH:  Heater OFF (0% power)
When GPIO13 = 50%, GPIO24 = HIGH: Heater ON (50% power)
When GPIO13 = 100%, GPIO24 = HIGH: Heater ON (100% power)
```

---

## Files to Modify

1. `/home/pi/hatchling/settings.yml`
   - Add `dir: 24` to `setup_pin` section

2. `/home/pi/hatchling/brood/workers/controller.py`
   - Initialize GPIO24 in `__init__()`
   - Set GPIO24 in `pid_controller()` or `__init__()`
   - Ensure GPIO24 stays HIGH during operation

