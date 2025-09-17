#!/bin/bash

# Start FastAPI Backend Server
echo "🚀 Starting Excel Generator Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/uploads
mkdir -p data

# Start the server
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "💚 Health Check: http://localhost:8000/api/files/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the app as a module from the project root
python -m app.main
