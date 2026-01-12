#!/bin/bash
# Startup script for the backend server

echo "Starting Ilan Legal App Backend..."

# Function to find suitable python
find_python() {
    if command -v python3.11 &> /dev/null; then
        echo "python3.11"
    elif command -v python3.12 &> /dev/null; then
        echo "python3.12"
    elif command -v python3.10 &> /dev/null; then
        echo "python3.10"
    elif command -v python3 &> /dev/null; then
        echo "python3"
    else
        return 1
    fi
}

PYTHON_CMD=$(find_python)

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Using Python interpreter: $PYTHON_CMD"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment with $PYTHON_CMD..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip to avoid build issues
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f "../.env" ]; then
    echo "Warning: .env file not found. Please create one with required environment variables."
fi

# Start the server
echo "Starting FastAPI server..."
# Add parent directory to PYTHONPATH to allow imports like 'from backend.config import settings'
export PYTHONPATH=$PYTHONPATH:$(cd .. && pwd)
python main.py

