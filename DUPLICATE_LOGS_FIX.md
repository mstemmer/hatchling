# Duplicate Log Entries with Multiprocessing Spawn - Solution

## Problem
Log messages were appearing multiple times in `hatch.log`:
```
2026-03-13 17:41:20 INFO: Hatchling startup initiated
2026-03-13 17:41:20 INFO: Starting new incubation from time point: 2026-03-13 17:41:19
2026-03-13 17:41:20 INFO: Load incubation program: chicken
2026-03-13 17:41:20 INFO: Hatchling startup initiated      ← DUPLICATE
2026-03-13 17:41:20 INFO: Starting new incubation from time point: 2026-03-13 17:41:19  ← DUPLICATE
2026-03-13 17:41:20 INFO: Load incubation program: chicken  ← DUPLICATE
```

## Root Cause
**Module-level code execution in spawned processes:**
- `hatchling.py` has module-level logging at lines 79-82 (outside any function)
- When using `multiprocessing.set_start_method('spawn')`, each child process is a **fresh Python interpreter**
- The fresh interpreter imports modules from scratch, including `hatchling.py`
- When `hatchling.py` is imported in the child process, the module-level code executes again
- Result: Each child process (controller, brood_lord, output) re-executes these log statements

## Solution
Wrap module-level logging with `if __name__ == '__main__'` check:

```python
# Only log startup messages in the main process
if __name__ == '__main__':
    logging.info('Hatchling startup initiated')
    logging.info(f'{init_status} from time point: {time_init}')
    
    if early_args.species:
        logging.info(f'Load incubation program: {early_args.species}')
```

This ensures:
- ✅ Logs only execute in the main process (when `hatchling.py --init --species chicken`)
- ✅ Logs are skipped when modules are imported in child processes
- ✅ No duplicate log entries
- ✅ `__name__ == '__main__'` guard at the bottom (`if __name__ == '__main__': Hatchling()`) is now consistent with module-level logging

## Technical Explanation

| Scenario | Before | After |
|----------|--------|-------|
| **Main process runs hatchling.py** | `__name__ == '__main__'` → logs execute | `__name__ == '__main__'` → logs execute |
| **Child process imports hatchling.py** | `__name__ == 'hatchling'` → logs execute (DUPLICATE!) | `__name__ == 'hatchling'` → logs skipped |

## Key Insight
- Module-level code (outside functions/classes) runs **every time the module is imported**
- With `spawn`, each child process imports all modules fresh
- Use `if __name__ == '__main__'` guard on any module-level code that should only run once

## Files Modified
- `hatchling.py`: Added `if __name__ == '__main__'` guard around startup logs (lines 79-82)
