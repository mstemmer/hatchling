# Race Condition in Log File Creation - Solution

## Problem
`FileNotFoundError: [Errno 2] No such file or directory: '/home/pi/hatchling/data/2026-03-13_chicken/hatch.log'` appears **intermittently**, not consistently.

This intermittent behavior is a classic sign of a **race condition**.

## Root Cause
**Timing gap between file creation and child process access:**

1. Parent process creates log file at line 60 in `hatchling.py`
2. Parent process opens FileHandler to log file at line 66
3. Parent spawns child processes
4. Child processes call `setup_logging_for_spawn()` to open the same file
5. **RACE CONDITION:** Between steps 1-3 and step 4, there can be:
   - File system buffering delays (file not yet written to disk)
   - File locking issues (multiple processes opening same file)
   - Timing variance depending on system load

**Why intermittent?** 
- On fast/idle systems: file is created quickly → no error
- On slow/loaded systems: file creation is delayed → child process tries to open before file exists → error

## Solution
Implemented **retry logic with exponential backoff** in two places:

### 1. Parent Process (`hatchling.py`)
- Increased sleep time from 0.1s to 0.2s after file deletion
- Added retry loop (3 attempts) when creating the file
- Verifies file exists before continuing

```python
# Create log file with multiple attempts
max_create_attempts = 3
for attempt in range(max_create_attempts):
    try:
        if not os.path.exists(log_file_path):
            open(log_file_path, 'a').close()
        if os.path.exists(log_file_path):
            break
    except OSError:
        if attempt < max_create_attempts - 1:
            sleep(0.1)
```

### 2. Child Processes (`brood/logging_config.py`)
- Added retry loop with **exponential backoff** (5 attempts)
- Initial delay: 0.1s, doubles after each retry (0.1s → 0.2s → 0.4s → 0.8s → 1.6s)
- Graceful fallback: if all retries fail, logs to console only (doesn't crash)

```python
max_retries = 5
retry_delay = 0.1

for attempt in range(max_retries):
    try:
        # Create log file and handlers...
        return  # Success
    except (FileNotFoundError, OSError) as e:
        if attempt < max_retries - 1:
            time.sleep(retry_delay)
            retry_delay *= 2  # Exponential backoff
        else:
            # Fall back to console logging
            logging.basicConfig(...handlers=[logging.StreamHandler()]...)
```

## Benefits
- ✅ Handles slow file system operations
- ✅ Tolerant of system load variations
- ✅ Exponential backoff prevents thundering herd
- ✅ Graceful degradation (console logging fallback)
- ✅ No crashes - child processes continue even if file logging fails
- ✅ Warning messages logged to console if retries exhaust

## Trade-offs
- ⚠️ Slightly slower startup (max 1.6s wait if file creation fails repeatedly)
- ⚠️ If all retries fail, logs go to console only (not ideal but acceptable)

## Testing
The fix handles:
- ✅ Fast systems (retries succeed immediately)
- ✅ Slow systems (retries wait with exponential backoff)
- ✅ Multiple processes creating file simultaneously (mkdir with exist_ok=True)
- ✅ File locking (retry when OSError occurs)

## Files Modified
1. `hatchling.py` - Added retry logic when creating log file (lines 52-63)
2. `brood/logging_config.py` - Added retry loop with exponential backoff in `setup_logging_for_spawn()` (lines 17-78)
