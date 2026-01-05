#!/bin/bash

# Kill background processes on exit
trap "kill 0" EXIT

echo "🚀 Starting PS5 Bot Dashboard..."

# Clean up old processes
echo "🧹 Bereinige alte Prozesse..."
fuser -k 8000/tcp > /dev/null 2>&1
fuser -k 3000/tcp > /dev/null 2>&1
fuser -k 3001/tcp > /dev/null 2>&1
killall -9 next-server > /dev/null 2>&1
killall -9 uvicorn > /dev/null 2>&1
# killall -9 python3 > /dev/null 2>&1 # Too aggressive for general use, commented out
sleep 2

# Start Backend
echo "📡 Starting Backend API (Port 8000)..."
cd dashboard/api
python3 main.py &
cd ../..

# Wait for backend
sleep 2

# Start Frontend
echo "💻 Starting Frontend (Port 3000)..."
cd dashboard
npm run dev
