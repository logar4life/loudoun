#!/bin/bash

# Start Xvfb virtual display
echo "Starting Xvfb virtual display..."
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
export DISPLAY=:99

# Wait a moment for Xvfb to start
sleep 2

# Start the application
echo "Starting Loudoun application..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 