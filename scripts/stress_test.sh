#!/bin/bash
# ============================================================
# VCC Assignment 3 - Stress Test Script
# Generates CPU and memory load to trigger auto-scaling
# ============================================================

echo "=========================================="
echo " Stress Test - Trigger Auto-Scaling"
echo "=========================================="
echo ""
echo "This script will push resource usage above 75%"
echo "to demonstrate the auto-scaling mechanism."
echo ""

# Check if stress-ng is installed
if ! command -v stress-ng &> /dev/null; then
    echo "Installing stress-ng..."
    sudo apt-get install -y stress-ng 2>/dev/null || {
        echo "stress-ng not available. Using Python-based stress test."
        echo "Sending stress request to Flask app..."
        curl -s http://localhost:5000/api/stress/cpu &
        curl -s http://localhost:5000/api/stress/memory &
        echo "Stress test triggered via API. Check the monitor logs."
        exit 0
    }
fi

echo "Select stress test type:"
echo "  1) CPU stress (push CPU > 75%)"
echo "  2) Memory stress (push Memory > 75%)"
echo "  3) Combined CPU + Memory stress"
echo "  4) Stop stress test"
echo ""
read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Starting CPU stress test for 120 seconds..."
        stress-ng --cpu $(nproc) --cpu-load 85 --timeout 120s
        ;;
    2)
        echo "Starting Memory stress test for 120 seconds..."
        stress-ng --vm 2 --vm-bytes 80% --timeout 120s
        ;;
    3)
        echo "Starting combined stress test for 120 seconds..."
        stress-ng --cpu $(nproc) --cpu-load 85 --vm 2 --vm-bytes 80% --timeout 120s
        ;;
    4)
        echo "Killing any running stress-ng processes..."
        killall stress-ng 2>/dev/null
        echo "Stress test stopped."
        ;;
    *)
        echo "Invalid choice."
        ;;
esac
