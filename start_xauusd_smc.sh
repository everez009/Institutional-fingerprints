#!/bin/bash

# XAUUSD SMC Monitor Startup Script

echo "=========================================="
echo "XAUUSD Smart Money Concepts Monitor"
echo "=========================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy .env.example to .env and add your Twelve Data API key:"
    echo "cp .env.example .env"
    echo ""
    echo "Then edit .env and add: TWELVE_DATA_API_KEY=your_api_key_here"
    exit 1
fi

# Check if TWELVE_DATA_API_KEY is set
if ! grep -q "TWELVE_DATA_API_KEY=" .env; then
    echo "❌ TWELVE_DATA_API_KEY not found in .env file!"
    echo "Please add your Twelve Data API key to .env"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Install dependencies if needed
if ! python3 -c "import aiohttp" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting XAUUSD SMC Monitor..."
echo "Monitor will run every 5 minutes"
echo "Press Ctrl+C to stop"
echo ""

# Start the monitor
python3 xauusd_smc_monitor.py
