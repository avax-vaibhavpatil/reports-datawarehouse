#!/bin/bash

# Start FastAPI Backend Server with Gunicorn
echo "🚀 Starting Excel Generator Backend with Gunicorn..."

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

# Start the server with Gunicorn
echo "🌐 Starting Gunicorn server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo "💚 Health Check: http://localhost:8000/api/files/health"
echo ""
echo "🔧 Gunicorn Configuration:"
echo "   - Workers: $(python -c 'import multiprocessing; print(multiprocessing.cpu_count() * 2 + 1)')"
echo "   - Worker Class: uvicorn.workers.UvicornWorker"
echo "   - Timeout: 30s"
echo "   - Max Requests: 1000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the app with Gunicorn
gunicorn -c gunicorn.conf.py app.main:app