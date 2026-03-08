# gpiozero PWM on RPi5 with Multiprocessing - Solution

## Problem
GPIO12 PWM control worked perfectly in standalone test scripts but failed when run inside a forked child process (via `multiprocessing.Process`).

## Root Cause
**Fork vs Spawn difference:**
- **fork()** (default): Child process inherits parent's memory state, including gpiozero's broken pin factory state after fork
- **spawn()** (new): Child process starts fresh Python interpreter, allowing gpiozero to initialize cleanly

When using `fork()`, gpiozero's pin factory initialization was stale/broken after the fork, preventing GPIO control from working.

## Solution
Switch from fork to spawn in `/home/pi/hatchling/brood/spawn.py`:

```python
from multiprocessing import Process, Queue, set_start_method

class SpawnHatchling():
    def __init__(self, config, inc_program, time_init, data_folder):
        # Use 'spawn' instead of 'fork' for multiprocessing
        try:
            set_start_method('spawn', force=True)
        except RuntimeError:
            pass  # Already set
        
        # ... rest of init ...
```

## What Changed
| Aspect | Before | After |
|--------|--------|-------|
| **Multiprocessing Method** | fork (default) | spawn |
| **Child Process Init** | Inherits broken pin factory | Fresh Python interpreter |
| **GPIO Control** | ❌ Not working | ✅ Working |
| **Performance** | Slightly faster | Slightly slower (startup overhead) |

## Controller Changes
No changes needed to `controller.py` - it already uses gpiozero correctly:
```python
from gpiozero import Device
Device.pin_factory = None  # Auto-detect
self.heat = PWMLED(config['setup_pin']['heat'])
self.heat.value = self.duty_cycle / 100.0  # 0.0-1.0 range
```

## Trade-offs
- ✅ **Pro**: GPIO/I2C/SPI work reliably in forked processes
- ✅ **Pro**: Simpler code (no manual pin factory workarounds)
- ⚠️ **Con**: ~50-100ms slower process startup (minimal for incubator)
- ⚠️ **Con**: Slightly higher memory overhead per process

## Testing
Verified working:
- ✅ `hardware_test_scripts/gpiozero_pwm_example.py` (standalone)
- ✅ `brood/workers/controller.py` (in spawned process)
- ✅ MDD10 heater responds to PWM commands
- ✅ Temperature control via PID

## Key Learnings
1. gpiozero is excellent for GPIO, but multiprocessing requires special handling
2. Forking shares broken state; spawning creates clean processes
3. Always test GPIO code inside the actual process context (not just standalone)
4. RPi5 dtoverlay configuration is working correctly (chip=0, channel=0 → GPIO12)
