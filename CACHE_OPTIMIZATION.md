# CSV Data Cache Optimization

## Problem
The original implementation had significant performance issues with large CSV files:

- **7 separate callbacks** each read the entire CSV file independently
- **Every 2 seconds**, the file was read 7 times (700% unnecessary I/O)
- No caching mechanism meant redundant reads even when data hadn't changed
- Memory bloat on resource-constrained Raspberry Pi systems
- File I/O bottleneck for long-running experiments (weeks/months of data)

### Example Impact
If `data.csv` is 100MB (typical for long-running incubator):
- **Old approach**: 700MB of I/O every 2 seconds
- **Result**: Memory exhaustion, UI slowdown, system strain

## Solution: Global DataCache Class

Implemented a `DataCache` class that:

1. **Maintains a single cached dataframe** in memory
2. **Tracks file modification time** (mtime) to detect changes
3. **Uses Time-To-Live (TTL)** of 500ms for cache validity
4. **Re-reads only when**:
   - File has been modified (mtime changed)
   - Cache TTL has expired (500ms)
   - File doesn't exist

### Architecture
```python
class DataCache:
    - df: Cached pandas DataFrame
    - last_mtime: File modification timestamp
    - last_read_time: Last cache read timestamp
    - cache_ttl: 0.5 seconds (500ms)
    
    get_data(): Returns cached data or re-reads if needed
```

## Performance Improvement

### Before
```
Interval: 2000ms (2 seconds)
Callbacks: 7
Reads per cycle: 7
Total I/O per second: 3.5 full file reads
```

### After
```
Interval: 2000ms (2 seconds)
Callbacks: 7
Reads per cycle: 1 (first callback triggers read, others use cache)
Total I/O per second: 0.5 full file reads per 500ms
Reduction: ~87% fewer I/O operations
```

### Memory Impact
For a 100MB file:
- **Before**: 700MB read, processed multiple times per cycle
- **After**: 100MB cached, reused across all callbacks
- **Savings**: ~600MB of wasted I/O per cycle

## Updated Callbacks

The following callbacks now use `data_cache.get_data()` instead of `pd.read_csv()`:

1. ✅ `update_temp_gauge()` - Temperature gauge
2. ✅ `update_humidity_gauge()` - Humidity gauge
3. ✅ `update_sensor_temp_0_box()` - Sensor 0 reading
4. ✅ `update_sensor_temp_1_box()` - Sensor 1 reading
5. ✅ `update_set_temp_box()` - Set temperature display
6. ✅ `update_env_temp_box()` - Set humidity display
7. ✅ `make_chart_day()` - Daily chart (10 min updates)

## Cache TTL Tuning

The cache TTL is set to **500ms** (0.5 seconds):
- **2-second interval callbacks**: Will see fresh data every ~2.5 updates
- **10-minute interval callbacks**: Effectively always use cached data
- **Flexibility**: Can be adjusted by changing `self.cache_ttl` in the DataCache class

To adjust:
```python
self.cache_ttl = 0.5  # Change this value (in seconds)
```

## Benefits

1. **Memory Efficiency**: Single cached dataframe instead of 7 simultaneous reads
2. **I/O Reduction**: ~87% fewer file operations
3. **Responsiveness**: Less strain on Raspberry Pi I/O subsystem
4. **Scalability**: Handles large files gracefully
5. **Smart Invalidation**: Automatically detects file changes via mtime
6. **Fault Tolerance**: Graceful handling of read errors

## Testing Recommendations

To verify the optimization works:

1. Monitor system CPU/IO during operation:
   ```bash
   iostat -x 1  # Watch %util column
   ```

2. Check memory usage:
   ```bash
   ps aux | grep monitor.py
   ```

3. Compare before/after with different file sizes

## Future Enhancements

- Add cache statistics logging (hit/miss ratio)
- Make TTL configurable via command-line argument
- Add optional gzip compression for cached data
- Consider SQLite backend for even larger datasets
