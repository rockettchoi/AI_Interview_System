#!/bin/bash

echo "======================================"
echo "AI Mock Interview System"
echo "======================================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Please copy .env.example to .env and configure your API keys:"
    echo "  cp .env.example .env"
    echo ""
    echo "Then edit .env and add your OpenAI API key."
    echo ""
    read -p "Press Enter to continue anyway or Ctrl+C to exit..."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Run the application
echo ""
echo "======================================"
echo "Starting Flask application..."
echo "======================================"
echo "Access the application at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
