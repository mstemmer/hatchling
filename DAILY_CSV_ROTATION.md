# Daily CSV File Rotation Implementation

## Overview

Implemented automatic daily CSV file rotation in `stream_data.py`. Each day's data is now stored in a separate dated file (`data_YYYY-MM-DD.csv`) with a symlink (`data.csv`) always pointing to the current day's file.

## Changes Made

### 1. Import Addition
- Added `timedelta` from `datetime` module for date arithmetic

### 2. Initialization (`__init__`)
Added day-tracking variables:
```python
self.current_day = datetime.now().date()
self.next_rotation_time = self.time_init + timedelta(days=1)
```

### 3. File Creation (`_create_file()`)
**Major changes:**
- Creates dated files: `data_2026-04-01.csv`, `data_2026-04-02.csv`, etc.
- Creates symlink: `data.csv` → `data_YYYY-MM-DD.csv`
- Handles existing files gracefully:
  - Removes old symlinks
  - Backs up non-symlink `data.csv` files to `data_old.csv`
- Fallback: If symlink creation fails (some filesystems), uses dated file directly

### 4. Daily Rotation Check (`_check_and_rotate_day()`) - NEW
Called every iteration of the data collection loop:
```python
def _check_and_rotate_day(self):
    """Check if a new day has started and rotate CSV file if needed"""
    # Detects day boundary crossing
    # Creates new dated file
    # Updates symlink to point to new file
    # Logs rotation events
```

Key features:
- Compares current date with `self.current_day`
- On boundary crossing, creates new file and updates symlink
- Logs previous and new file paths
- Updates `self.current_day` and `self.next_rotation_time`

### 5. Output Loop (`output()`)
Added rotation check at the start of each loop iteration:
```python
while True:
    try:
        # Check if we need to rotate to a new day
        self._check_and_rotate_day()
        # ... rest of data collection
```

## File Structure After Implementation

Before:
```
data_folder/
├── data.csv              (single file, grows indefinitely)
└── hatch.log
```

After:
```
data_folder/
├── data_2026-04-01.csv   (Day 1 data)
├── data_2026-04-02.csv   (Day 2 data)
├── data_2026-04-03.csv   (Day 3 data, current)
├── data.csv              (symlink → data_2026-04-03.csv)
└── hatch.log
```

## Monitor Compatibility

✅ **Monitor.py works transparently:**
- Monitor reads `data.csv` (via symlink)
- Cache invalidation works automatically:
  - `data.csv` target changes → cache detects mtime change
  - Automatic re-read on new day
  - No manual restart required

## Behavior Details

### Rotation Timing
- **Trigger**: Daily at midnight (system time)
- **Frequency**: Once per day
- **Check**: Every data collection iteration (~1 second interval)
- **Cost**: Minimal - simple date comparison (O(1))

### File Naming
- Format: `data_YYYY-MM-DD.csv`
- Examples: `data_2026-04-01.csv`, `data_2026-04-15.csv`
- ISO 8601 compliant for easy sorting/parsing

### Symlink Behavior
- Always points to **current day's file**
- Automatically updated on day boundary
- Monitor reads symlink transparently
- Works on Linux/Unix systems
- Windows: Falls back to using dated file directly (due to symlink limitations)

### Error Handling
- **Symlink creation failure**: Falls back to returning dated file path
- **File rotation failure**: Logged, continues with current file
- **Missing dated file**: Creates it with headers
- **Existing dated file**: Reuses (appends data)

## Logging

New log messages:
```
INFO: Created dated CSV file: /path/to/data_2026-04-01.csv
INFO: Created symlink: data.csv -> data_2026-04-01.csv
INFO: Day boundary crossed: 2026-04-01 -> 2026-04-02
INFO: Rotated to new day's CSV: /path/to/data.csv
INFO: Previous day's file: /path/to/data_2026-04-01.csv
```

## Performance Impact

- **CPU**: Negligible
  - Single date comparison per iteration
  - File operations only on day boundary (once per 24 hours)
  
- **I/O**: Minimal
  - No additional writes (same data)
  - Symlink update: Single filesystem operation
  - Old files remain accessible

- **Disk**: Same usage
  - Total data size identical
  - Just split across multiple files
  
- **Memory**: No change
  - Data cache behavior unchanged
  - Monitor processes identically

## Backward Compatibility

- ✅ Existing monitor works without changes
- ✅ Cache system transparent to rotation
- ✅ Old `data.csv` files backed up if found
- ✅ Gradual transition possible

## Testing Recommendations

1. **Normal operation**: Let run for 24+ hours, verify:
   - Day 1: `data_2026-04-01.csv` created
   - Day 2: New `data_2026-04-02.csv` created, symlink updated
   - Monitor continues functioning without restart

2. **Monitor verification**:
   ```bash
   # Monitor should work transparently
   cd /home/pi/hatchling
   python -m brood.workers.monitor --input data/2026-04-01_chicken
   ```

3. **Symlink verification**:
   ```bash
   ls -la data/2026-04-01_chicken/data.csv
   # Should show: data.csv -> data_2026-04-01.csv
   ```

4. **Log inspection**:
   ```bash
   tail -f data/2026-04-01_chicken/hatch.log | grep "Day boundary\|Rotated"
   ```

## Future Enhancements

- Archive old files to compressed format (gzip)
- Implement retention policy (keep only last N days)
- Add metadata tracking (days completed, data points per day)
- Web UI to view all days of data
- Automatic daily report generation
