# Heat Element Over-Heating Issue - Root Cause Analysis

## Problems Identified in controller.py

### 1. **CRITICAL: Incorrect Initial Setpoint (Line 80)**
```python
self.pid = PID(290, 70, 10, setpoint=37)  # ❌ Wrong!
```
- Setpoint is set to **37°C**, but target should be **37.8°C** (chicken incubation)
- This causes the PID to think it needs to heat until 37°C is reached
- Once at 37.8°C, the PID error is positive (37.8 - 37 = 0.8), causing continued heating

**Fix:**
```python
self.pid = PID(290, 70, 10, setpoint=37.8)  # ✓ Correct
```

### 2. **CRITICAL: Wrong Default Set Temperature (Line 94)**
```python
self.set_humid, self.set_temp = [55, 36]  # ❌ set_temp = 36°C
```
- Default set_temp is **36°C**, which is below the actual operating point
- This should be **37.8°C** for chicken
- If `read_program()` doesn't receive new values quickly, controller heats to 36°C minimum

**Fix:**
```python
self.set_humid, self.set_temp = [55, 37.8]  # ✓ Correct
```

### 3. **Redundant PID Initialization (Lines 80, 84)**
```python
self.pid = PID(290, 70, 10, setpoint=37)           # Initialize with these values...
self.pid.tunings = (config["PID_parameters"])      # ...then immediately override them
```
- The initial `(290, 70, 10)` are meaningless since they're overwritten
- Keep only the override from config

### 4. **Potential Issue: PID Sample Time (Line 83)**
```python
self.pid.sample_time = None
```
- This means PID doesn't wait between updates
- Combined with the control loop that runs continuously, this could cause aggressive oscillations
- Should be set to ~1 second to match the sensor read interval

## Why Heater Keeps Running

1. Initial setpoint is 37°C (too low)
2. When actual temp reaches 37.8°C, error = 37.8 - 37 = +0.8°C
3. Positive error means "too hot" but setpoint is still below target
4. PID may not reduce duty cycle enough because of integral windup
5. Heater continues operating until it hits the hardcoded initial setpoint of 37°C

## Recommended Fixes

```python
# Line 80 - Fix initial setpoint
self.pid = PID(290, 70, 10, setpoint=37.8)  # Use actual target

# Line 83 - Set appropriate sample time
self.pid.sample_time = 1.0  # 1 second between samples

# Line 94 - Fix default set_temp
self.set_humid, self.set_temp = [55, 37.8]  # Match target
```

## Additional Recommendations

1. Add anti-windup to PID (prevent integral term from growing when saturated)
2. Monitor duty cycle output to verify PID is reducing it above setpoint
3. Add debugging logs to track setpoint vs. actual temperature
