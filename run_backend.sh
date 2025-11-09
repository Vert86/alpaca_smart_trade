#!/bin/bash

# Alpaca Smart Trade - Backend Startup Script

echo "================================================"
echo "Alpaca Smart Trade - Starting Backend Server"
echo "================================================"
echo ""

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "Checking dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies ready"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  WARNING: .env file not found!"
    echo "Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "Please edit .env file with your Alpaca API credentials:"
    echo "  nano .env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo ""
echo "================================================"
echo "Starting Flask server..."
echo "================================================"
echo ""

# Start the backend server
python app/api.py
