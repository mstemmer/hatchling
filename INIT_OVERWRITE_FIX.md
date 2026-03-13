# Init Overwrite Fix - Handling Existing Data

## Problem
When running with `--init` on an existing incubation (files already created from a previous run):
- Old log file was deleted
- New file creation failed intermittently
- `FileNotFoundError` occurred

This happened because:
1. Old `hatch.log` deleted
2. New file creation started but wasn't completed fast enough
3. Child processes started and found no log file
4. Race condition between deletion and creation

## Solution

### 1. Parent Process (`hatchling.py`)
**Enhanced cleanup and creation logic:**

```python
# When starting new incubation, delete old files to start fresh
if early_args.init:
    # Delete old log file if it exists
    if os.path.exists(log_file_path):
        try:
            os.remove(log_file_path)
            sleep(0.2)  # Ensure file system has time to delete
        except OSError as e:
            print(f"WARNING: Could not delete old log file: {e}")
    
    # Also delete old data file if it exists
    data_file_path = os.path.join(time_species_path, 'data.csv')
    if os.path.exists(data_file_path):
        try:
            os.remove(data_file_path)
        except OSError as e:
            print(f"WARNING: Could not delete old data file: {e}")

# Create fresh log file for this run
max_create_attempts = 5
for attempt in range(max_create_attempts):
    try:
        # Always create fresh file (overwrite mode 'w')
        with open(log_file_path, 'w') as f:
            pass  # Create empty file
        if os.path.exists(log_file_path):
            break
    except OSError as e:
        if attempt < max_create_attempts - 1:
            sleep(0.1 * (attempt + 1))  # Progressive delay
        else:
            # Report error and exit
            sys.exit("--> Exiting program")
```

**Key improvements:**
- ✅ Opens file in write mode (`'w'`) to ensure it's fresh/overwritten
- ✅ Better error handling with try/except blocks
- ✅ Progressive delay (not just fixed delay)
- ✅ Cleans up both log and data files on `--init`

### 2. Child Processes (`brood/logging_config.py`)
**Improved retry logic:**

```python
# Retry logic with exponential backoff
max_retries = 10  # Increased from 5
base_delay = 0.05  # Shorter initial delay

for attempt in range(max_retries):
    try:
        # Wait for log file to be accessible
        if not os.path.exists(log_file_path):
            if attempt < max_retries - 1:
                time.sleep(base_delay * (2 ** attempt))  # Exponential backoff
                continue
            else:
                # Last attempt - create it ourselves as fallback
                with open(log_file_path, 'a') as f:
                    pass
        
        # Set up file handler with append mode
        file_handler = logging.FileHandler(log_file_path, mode='a')
        # ... rest of setup ...
        return  # Success
        
    except (FileNotFoundError, OSError, IOError) as e:
        if attempt < max_retries - 1:
            time.sleep(base_delay * (2 ** attempt))
        else:
            # Graceful fallback to console-only logging
            # Don't crash - just log warning
            logging.warning("Using console logging only")
            return
```

**Key improvements:**
- ✅ Increased retries from 5 to 10
- ✅ Shorter initial delay for faster first attempts
- ✅ Exponential backoff with formula `2^attempt`
- ✅ Fallback: creates file itself if parent hasn't yet
- ✅ Graceful degradation: continues with console-only logging instead of crashing

## Behavior with `--init`

| Scenario | Before | After |
|----------|--------|-------|
| **First run** | Create log file | ✅ Create fresh log file |
| **Resume run** | Append to log | ✅ Append to log |
| **Re-init existing** | Delete, create, race condition | ✅ Delete both files, create fresh, retry on fail |
| **Slow system** | May fail intermittently | ✅ Retry 10 times with exponential backoff |
| **File locked** | Crash with error | ✅ Retry, fallback to console logging |

## Usage

**Start new incubation (overwrites old):**
```bash
python hatchling.py --init --species chicken
```
- ✅ Old `hatch.log` deleted
- ✅ Old `data.csv` deleted
- ✅ Fresh log file created
- ✅ Fresh data file created

**Resume existing incubation:**
```bash
python hatchling.py --species chicken
```
- ✅ Appends to existing `hatch.log`
- ✅ Appends to existing `data.csv`

## Files Modified
1. `hatchling.py` - Enhanced cleanup and creation (lines 52-84)
2. `brood/logging_config.py` - Improved retry logic in `setup_logging_for_spawn()` (lines 17-99)
