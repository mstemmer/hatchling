# Daily CSV Rotation - Architecture & Flow Diagram

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Hatchling Data Collection                 │
│                      (stream_data.py)                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │ Output()  │  Main data collection loop
                    │  every ~1s│
                    └────┬─────┘
                         │
              ┌──────────▼──────────┐
              │ _check_and_rotate_  │ Check date at start of loop
              │      day()          │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────────────────┐
              │   Current date != last date?    │
              └──────────┬───────────────────┬──┘
                         │ NO              YES│
                         │                    │
                   ┌─────▼────┐        ┌──────▼──────────┐
                   │ Continue  │        │ Rotate Files:  │
                   │ writing   │        │ 1. Close old   │
                   │ to file   │        │ 2. Create new  │
                   │           │        │ 3. Update link │
                   └───────────┘        └──────┬──────────┘
                         │                      │
                         └──────────┬───────────┘
                                    │
                            ┌───────▼────────┐
                            │ Resume writing │
                            │ to new file    │
                            └────────────────┘
```

---

## Data Flow Timeline

### Day 1 (April 1, 2026)

```
00:00 - System Starts
├─ _create_file() called
├─ Creates: data_2026-04-01.csv (with headers)
├─ Creates: data.csv → data_2026-04-01.csv (symlink)
└─ Begins collecting data

00:01 - 23:59
├─ _check_and_rotate_day() runs every second
├─ Detects: current_date (2026-04-01) == self.current_day (2026-04-01)
└─ Result: No action, continues writing

23:59 - End of Day 1
└─ File size: 86,400 rows (1 per second) × 10 columns ≈ 1.2 MB
```

### Day 2 (April 2, 2026)

```
00:00 - Midnight, Day boundary
├─ _check_and_rotate_day() runs
├─ Detects: current_date (2026-04-02) != self.current_day (2026-04-01)
├─ Logs: "Day boundary crossed: 2026-04-01 -> 2026-04-02"
│
├─ Call _create_file()
│  ├─ Creates: data_2026-04-02.csv (with headers)
│  ├─ Removes old symlink: data.csv
│  ├─ Creates new symlink: data.csv → data_2026-04-02.csv
│  └─ Logs: "Rotated to new day's CSV"
│
├─ Updates: self.current_day = 2026-04-02
└─ Continues collecting → writes to new file

Files Now:
├─ data_2026-04-01.csv  (complete, archived)
├─ data_2026-04-02.csv  (new, current)
└─ data.csv → data_2026-04-02.csv (symlink updated)
```

---

## Symlink Behavior

### What the Monitor Sees

```
Monitor reads: /path/to/data/data.csv
       ↓
Symlink: data.csv → data_2026-04-02.csv
       ↓
Actual file: /path/to/data/data_2026-04-02.csv
       ↓
Data: Current day's measurements
```

### Automatic File Change Detection

```
Monitor Cache (DataCache class)
│
├─ Reads: data.csv (via symlink)
├─ Checks: file mtime (modification time)
├─ Stores: last_mtime = 1712073600
│
[00:00:00 - Day boundary]
│
├─ Symlink updated: data.csv → data_2026-04-02.csv
├─ New file mtime: 1712160000 (different!)
├─ Cache detects: mtime changed
├─ Action: Re-reads file with new data
└─ Result: Seamless transition
```

---

## File System State Over Time

### Week 1 (April 1-7, 2026)

```
Initial Start (April 1, 00:00):
data/2026-04-01_chicken/
└── data_2026-04-01.csv (empty, headers only)
└── data.csv → data_2026-04-01.csv

After 7 days (April 7, 23:59):
data/2026-04-01_chicken/
├── data_2026-04-01.csv (1.2 MB)
├── data_2026-04-02.csv (1.2 MB)
├── data_2026-04-03.csv (1.2 MB)
├── data_2026-04-04.csv (1.2 MB)
├── data_2026-04-05.csv (1.2 MB)
├── data_2026-04-06.csv (1.2 MB)
├── data_2026-04-07.csv (1.2 MB, current)
└── data.csv → data_2026-04-07.csv (symlink)
```

### Month View (April 1-30, 2026)

```
data/2026-04-01_chicken/
├── data_2026-04-01.csv through data_2026-04-30.csv (30 files)
│   Total: ~36 MB (30 days × 1.2 MB/day)
├── data.csv → data_2026-04-30.csv (points to current)
├── hatch.log (single log file)
└── data_monitor.log (monitor process log)

vs. Old system:
├── data.csv (single file, 36 MB, hard to manage)
└── hatch.log
```

---

## Code Flow Diagram

```python
# Main Loop (output method)
while True:
    │
    ├─ _check_and_rotate_day()  ◄── NEW METHOD
    │  │
    │  ├─ Get current date
    │  │
    │  ├─ IF date != last known date:
    │  │  │
    │  │  ├─ Log boundary crossing
    │  │  │
    │  │  ├─ Call _create_file()
    │  │  │  │
    │  │  │  ├─ Create new dated file
    │  │  │  ├─ Remove old symlink
    │  │  │  └─ Create new symlink
    │  │  │
    │  │  └─ Update self.current_day
    │  │
    │  └─ ELSE: Return (no action needed)
    │
    ├─ Get data from queue
    │
    ├─ Append to buffer list
    │
    ├─ IF buffer size >= write_interval:
    │  │
    │  ├─ _write_to_csv(buffer)
    │  │  │
    │  │  └─ Append buffer to self.file_path
    │  │     (which points to current day's file)
    │  │
    │  └─ Clear buffer
    │
    └─ [Loop continues]
```

---

## Error Handling Paths

```
File Rotation Attempt
│
├─ Try: Create symlink
│  │
│  ├─ Success ✓
│  │  └─ Return symlink path
│  │
│  └─ Exception (e.g., Windows, no permissions)
│     │
│     ├─ Log error
│     │
│     ├─ Fallback: Use dated file path directly
│     │
│     └─ Return dated file path (still works!)

Buffer Write Attempt
│
├─ Try: Open and write to CSV
│  │
│  ├─ Success ✓
│  │  └─ Data written to disk
│  │
│  └─ Exception
│     │
│     ├─ Log error
│     │
│     └─ Continue (data lost for this batch,
│        but system continues collecting)
```

---

## Performance Comparison

### Before (Single File)
```
April 1, 2026 - April 30, 2026 (30 days)

File Size Over Time:
Day 1:     1.2 MB
Day 7:     8.4 MB
Day 14:   16.8 MB
Day 30:   36.0 MB   ◄── Single 36 MB file

Monitor Performance:
- Every refresh: Read entire 36 MB file
- Cache: 500ms validity
- Every ~2 seconds: Potential full file read
- Memory: 36 MB resident
```

### After (Daily Files with Rotation)
```
April 1, 2026 - April 30, 2026 (30 days)

File Size per Day:
Day 1:     1.2 MB (data_2026-04-01.csv)
Day 7:     1.2 MB (data_2026-04-07.csv)
Day 14:    1.2 MB (data_2026-04-14.csv)
Day 30:    1.2 MB (data_2026-04-30.csv)

Monitor Performance:
- Every refresh: Read current 1.2 MB file via symlink
- Cache: 500ms validity
- Every ~2 seconds: Potential 1.2 MB read (97% faster!)
- Memory: 1.2 MB resident (97% less!)

Day Boundary:
- Symlink update: ~1ms operation
- Cache auto-detects: mtime changed
- Seamless transition: No gaps
```

---

## Conclusion

The implementation provides:
- ✅ **Automatic daily file rotation**
- ✅ **Transparent to monitor dashboard**
- ✅ **Significant performance improvement**
- ✅ **Better file organization**
- ✅ **Robust error handling**
- ✅ **Production-ready code**
