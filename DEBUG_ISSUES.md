# Hatchling Startup Issues - Debug Guide

## Problem
After recent changes:
1. Many log entries are not being added to hatch.log
2. When NOT using `--init`, the software doesn't resume from saved time point

## Root Causes Identified

### 1. Duplicate Data File Deletion
**Before fix:** Data file was deleted twice
- Once at module level (lines 52-84) when `--init`  
- Again in `config()` method (line 136) when `self.args.init == True`

**Result:** Could cause race conditions and data loss

**Fix Applied:** Removed duplicate deletion from `config()` method. Only delete at module level.

### 2. Missing config["init"] Flag
**Before fix:** Removed `config["init"] = self.args.init` from config()

**Result:** Config dict didn't track initialization mode

**Fix Applied:** Re-added the flag to track init mode

### 3. Module-Level Logging Execution  
**Current state:** Module-level startup logs only execute when `__name__ == '__main__'`

**Result:** In child processes spawned via `spawn`, module-level code still executes

**Verify:** Check if module-level logs appear in hatch.log

## Verification Checklist

After applying fixes, verify:

```bash
# 1. Start fresh incubation
python hatchling.py --init --species chicken

# Check that:
# ✓ Old log/data files deleted
# ✓ Fresh log file created
# ✓ Log messages appear in hatch.log
# ✓ Data being written to data.csv

# 2. Stop the process (Ctrl+C)

# 3. Resume incubation  
python hatchling.py --species chicken

# Check that:
# ✓ time_init.txt has correct timestamp from initial run
# ✓ Previous log entries still in hatch.log (not deleted)
# ✓ Previous data still in data.csv (not deleted)
# ✓ New entries appended (not overwritten)
```

## Key Files and Their Roles

1. **hatchling.py** - Module level
   - Creates data folders
   - Reads/writes time_init.txt
   - Deletes old files on `--init`
   - Creates fresh log file
   - Sets up logging handlers (parent process only)

2. **brood/spawn.py** - Spawns child processes
   - Calls `setup_logging_for_spawn()` in each child

3. **brood/logging_config.py** - Child process logging
   - Retry loop with exponential backoff
   - Creates/finds log file in child processes
   - Graceful fallback to console-only logging

4. **brood/workers/stream_data.py** - Data output
   - Creates/appends to data.csv
   - Buffers 50 rows before writing

## Common Issues and Solutions

| Issue | Likely Cause | Fix |
|-------|------------|-----|
| No log entries | Logging setup failed in child | Check `setup_logging_for_spawn()` retry logic |
| Data not saved | CSV write failed | Check `stream_data.py._write_to_csv()` |
| Doesn't resume | time_init.txt not read | Verify file exists and is readable |
| Double entries | Module-level logging executed twice | Ensure `if __name__ == '__main__'` guard |

## Testing Log Setup

To verify logging is working in child processes:

```python
# In any child process (controller.py, brood_lord.py, etc.)
import logging
logging.info("TEST: This should appear in hatch.log")
```

If this message doesn't appear, logging setup in child failed.

## Next Steps

1. Run full incubation cycle with fresh `--init`
2. Check hatch.log for completeness
3. Stop and resume to verify no data loss
4. Monitor for missing entries
