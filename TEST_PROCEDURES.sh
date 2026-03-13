#!/bin/bash
# Quick test to verify hatchling startup and logging

echo "=== Hatchling Startup Test ==="
echo ""

# Test 1: Fresh start
echo "Test 1: Fresh start with --init --species chicken"
echo "This should:"
echo "  - Create new data/2026-03-13_chicken/ directory"  
echo "  - Create fresh hatch.log (no old entries)"
echo "  - Log 'Hatchling startup initiated'"
echo "  - Log 'Starting new incubation'"
echo "  - Log 'Load incubation program: chicken'"
echo ""
echo "Command to run:"
echo "  python /home/pi/hatchling/hatchling.py --init --species chicken"
echo ""
echo "Then check:"
echo "  tail -f /home/pi/hatchling/data/2026-03-13_chicken/hatch.log"
echo ""
echo "=================="
echo ""

# Test 2: Resume
echo "Test 2: After stopping (Ctrl+C), resume without --init"
echo "This should:"
echo "  - NOT delete old log/data files"
echo "  - Read time_init.txt from initial run"
echo "  - APPEND to hatch.log (not create new)"
echo "  - APPEND to data.csv (not create new)"
echo ""
echo "Command to run:"
echo "  python /home/pi/hatchling/hatchling.py --species chicken"
echo ""
echo "Then check:"
echo "  # Log entries should have same date as first run"
echo "  grep 'Load incubation program' /home/pi/hatchling/data/2026-03-13_chicken/hatch.log"
echo "  # Should appear only ONCE (not duplicated)"
echo ""
echo "=================="
echo ""

# Test 3: Check time_init.txt
echo "Test 3: Verify time_init.txt"
echo ""
echo "Should contain timestamp from first run (unchanged):"
echo "  cat /home/pi/hatchling/data/time_init.txt"
echo ""
