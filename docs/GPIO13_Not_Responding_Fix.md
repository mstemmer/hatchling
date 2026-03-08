# GPIO13 PWM Not Responding - Root Cause Analysis

## Critical Bugs Found & Fixed

### **Bug #1: PID Setpoint = 10°C ❌ CRITICAL**
```python
# BEFORE (Line 82):
self.pid = PID(..., setpoint=10)

# AFTER:
self.pid = PID(..., setpoint=37.8)
```

**Why this broke GPIO13:**
- Room temperature: ~26°C
- PID setpoint: 10°C
- Error = 10 - 26 = **-16°C** (system thinks it's OVERHEATING)
- PID output: **NEGATIVE error** → duty cycle = 0%
- Heater duty stays at 0% regardless of temperature!

**Result**: GPIO13 gets `ChangeDutyCycle(0)` constantly → pin stays LOW → No response to duty changes

---

### **Bug #2: Default Set_Temp = 10°C ❌ CRITICAL**
```python
# BEFORE (Line 96):
self.set_humid, self.set_temp = [55, 10]

# AFTER:
self.set_humid, self.set_temp = [55, 37.8]
```

**Why this broke:**
- If `read_program()` hasn't received values from BroodLord yet
- Heater tries to heat to 10°C (below room temperature!)
- PID sees error as negative → duty = 0%

---

### **Bug #3: PID Tunings NOT Applied ❌ CRITICAL**
```python
# BEFORE (Line 85 - COMMENTED OUT):
# self.pid.tunings = (config["PID_parameters"])

# AFTER:
self.pid.tunings = (config["PID_parameters"])
```

**Why this broke:**
- Config has: `PID_parameters: [260, 85, 12]`
- But PID initialized with: `(290, 70, 10)` from constructor
- Line 85 should override, but it was commented!
- PID runs with wrong parameters
- Response is sluggish and doesn't adapt to temperature changes

---

### **Bug #4: Sample Time NOT Set ❌ CRITICAL**
```python
# BEFORE (Line 84 - COMMENTED OUT):
# self.pid.sample_time = 1.0

# AFTER:
self.pid.sample_time = 1.0
```

**Why this broke:**
- Without sample_time, PID calculates output every loop iteration
- Control loop runs ~0.2s (two sensor reads + processing)
- PID updates ~5 times per second
- **Integral term builds up too fast** → integral windup
- Causes oscillations and overshoot
- Duty cycle becomes erratic

---

## Verification Checklist

After fix, verify:

- [ ] **Temperature stabilizes at ~37.8°C**
- [ ] **Duty cycle changes smoothly** (not stuck at 0%)
- [ ] **GPIO13 voltage responds** to duty cycle:
  - 0% → ~0V
  - 50% → ~1.65V
  - 100% → ~3.3V
- [ ] **Log shows proper PID parameters**: `Initializing PID controller`
- [ ] **No oscillations** in temperature (should be stable ±0.5°C)
- [ ] **Heater gradually reduces** duty as temp approaches setpoint

---

## Data Flow Now Fixed

```
BroodLord sends target temp (37.8°C)
    ↓
read_program() updates self.set_temp = 37.8
    ↓
pid.setpoint = 37.8
    ↓
pid_controller() reads current_temp from sensors
    ↓
error = 37.8 - current_temp
    ↓
PID calculates output with proper Kp=260, Ki=85, Kd=12
    ↓
duty_cycle = PID(current_temp)  # Now responds properly!
    ↓
self.heat.ChangeDutyCycle(duty_cycle)  # GPIO13 changes!
```

---

## Expected Behavior After Fix

### Initial State (Room Temp ~26°C)
- Error = +11.8°C (need to heat)
- Duty cycle = **HIGH** (maybe 80-100%)
- GPIO13 = **HIGH** (heater ON)
- Temperature rises

### At Setpoint (37.8°C)
- Error ≈ 0°C (perfect)
- Duty cycle = **~48%** (steady-state to maintain temp)
- GPIO13 = **oscillating** at 48% frequency
- Temperature stable

### Above Setpoint (38.5°C)
- Error = **-0.7°C** (too hot)
- Duty cycle = **LOW** (maybe 30-40%)
- GPIO13 = **reduces frequency**
- Temperature falls back to 37.8°C

---

## Quick Test

1. Watch the log file:
   ```bash
   tail -f /home/pi/hatchling/data/2026-03-08_chicken/hatch.log
   ```

2. Check duty cycle in CSV:
   ```bash
   tail -20 /home/pi/hatchling/data/2026-03-08_chicken/data.csv | cut -d',' -f10
   ```
   Should see values changing, not stuck at 0 or 100

3. Monitor GPIO13 with multimeter or oscilloscope
   - Should see voltage change from 0V → 1.65V → 3.3V
   - Frequency changes with duty cycle

