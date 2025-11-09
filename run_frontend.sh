#!/bin/bash

# Alpaca Smart Trade - Frontend Startup Script

echo "================================================"
echo "Alpaca Smart Trade - Starting Frontend"
echo "================================================"
echo ""

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Dependencies not found. Installing..."
    npm install
    echo "✓ Dependencies installed"
fi

echo ""
echo "================================================"
echo "Starting React development server..."
echo "================================================"
echo ""
echo "Frontend will open at http://localhost:3000"
echo "Make sure the backend is running on port 5000"
echo ""

# Start the frontend server
npm start
