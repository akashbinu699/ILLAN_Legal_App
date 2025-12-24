#!/bin/bash
# Startup script for the backend server

echo "Starting Ilan Legal App Backend..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "Warning: .env file not found. Please create one with required environment variables."
fi

# Start the server
echo "Starting FastAPI server..."
python main.py

