#!/bin/bash
# ============================================================
# VCC Assignment 3 - Start Application and Monitor
# ============================================================

set -e

echo "=========================================="
echo " Starting VCC Auto-Scale Demo"
echo "=========================================="

# Load config
if [ -f config/gcp_config.env ]; then
    export $(grep -v '^#' config/gcp_config.env | xargs)
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start Flask application in background
echo "[1/2] Starting Flask application on port 5000..."
python src/app.py &
APP_PID=$!
echo "Flask app started (PID: $APP_PID)"

# Wait for app to start
sleep 2

# Start resource monitor
echo "[2/2] Starting resource monitor..."
echo "Threshold: ${THRESHOLD_PERCENT:-75}%"
echo "Check interval: ${CHECK_INTERVAL_SECONDS:-10}s"
echo ""
echo "Open http://localhost:5000 in your browser"
echo "Press Ctrl+C to stop both processes"
echo ""

# Trap Ctrl+C to stop both processes
trap "echo 'Stopping...'; kill $APP_PID 2>/dev/null; exit" SIGINT SIGTERM

python src/monitor.py

# If monitor exits, stop the app too
kill $APP_PID 2>/dev/null
