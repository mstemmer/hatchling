# Logging with Multiprocessing `spawn` - Solution

## Problem
When using `multiprocessing.set_start_method('spawn')`, child processes failed with:
```
FileNotFoundError: [Errno 2] No such file or directory: '/home/pi/hatchling/data/2026-03-12_chicken/hatch.log'
```

## Root Cause
**Fresh Interpreter vs. Inherited State:**
- Parent process (`hatchling.py`) sets up logging file handlers correctly before spawning
- Child processes (`controller.py`, `brood_lord.py`, `stream_data.py`) are fresh Python interpreters via `spawn`
- Fresh interpreters don't inherit parent's logging configuration (file handlers)
- Child processes attempt to use `logging.info()` but have no file handlers configured
- Result: Logging fails when trying to write to the unhandled log file

## Solution
Configure logging **inside each child process** before it runs:

### 1. Add logging setup function to `brood/logging_config.py`
```python
def setup_logging_for_spawn(log_file_path):
    """Configure logging for spawned child processes."""
    # Clear existing handlers
    logger = logging.getLogger()
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Set up file and console handlers
    log_format = logging.Formatter(...)
    file_handler = logging.FileHandler(log_file_path)
    # ... configure handlers ...
```

### 2. Update `brood/spawn.py` to call setup before running processes
```python
def run_controller(self, config, q_prog, q_data):
    setup_logging_for_spawn(self.log_file_path)  # ← Call this first
    BroodController(config, q_prog, q_data)
```

### 3. Pass log file path from parent to spawned children
```python
# hatchling.py passes log_file_path to SpawnHatchling
SpawnHatchling(config, inc_program, time_init, data_folder, log_file_path)

# SpawnHatchling stores and passes to each child process
class SpawnHatchling:
    def __init__(self, ..., log_file_path):
        self.log_file_path = log_file_path
```

## What Changed
| Component | Before | After |
|-----------|--------|-------|
| **Child Process Logging** | None (uses inherited parent config) | Set up via `setup_logging_for_spawn()` |
| **File Handler** | Missing in children | Configured in each child |
| **Log File Path** | Not passed to children | Passed via `SpawnHatchling.__init__` |
| **Result** | ❌ FileNotFoundError | ✅ Logging works in all processes |

## Key Files Modified
1. `brood/logging_config.py` - Added `setup_logging_for_spawn()` function
2. `brood/spawn.py` - Calls logging setup in each `run_*()` method
3. `hatchling.py` - Passes `log_file_path` to `SpawnHatchling`

## Technical Details
- Each spawned process is a **fresh Python interpreter** that imports modules anew
- The parent's logging configuration (file handlers) are **not inherited** by fresh processes
- Calling `setup_logging_for_spawn(log_file_path)` in each child:
  - Clears any default handlers
  - Creates fresh file and console handlers
  - Points them to the correct log file
  - Works because log file directory exists before spawning

## Testing Verified
- ✅ Log file created correctly at startup
- ✅ All child processes can write to log file
- ✅ No FileNotFoundError on spawn with logging
- ✅ Concurrent logging from multiple processes works
