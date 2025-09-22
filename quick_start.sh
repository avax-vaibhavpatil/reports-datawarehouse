#!/bin/bash

# 🚀 Excel Generator - Quick Start Script
# This script sets up and starts the entire application

set -e  # Exit on any error

echo "🎉 Welcome to Excel Generator!"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "requirements.txt" ] || [ ! -d "frontend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

print_status "Starting Excel Generator setup..."

# Check Python version
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.12+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if [ "$(printf '%s\n' "3.12" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.12" ]; then
    print_warning "Python version $PYTHON_VERSION detected. Python 3.12+ is recommended."
fi

# Check Node.js version
print_status "Checking Node.js version..."
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    print_status "Installation commands:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install nodejs npm"
    echo "  macOS: brew install node"
    echo "  Windows: Download from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version $(node --version) detected. Node.js 18+ is required."
    exit 1
fi

print_success "Python $(python3 --version) and Node.js $(node --version) are compatible"

# Setup Backend
print_status "Setting up FastAPI backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create data directories
print_status "Creating data directories..."
mkdir -p data/uploads
mkdir -p data

# Setup PostgreSQL Database
print_status "Setting up PostgreSQL database..."
if command -v psql &> /dev/null; then
    print_status "PostgreSQL detected. Setting up database..."
    python3 setup_database.py
    print_success "Database setup complete!"
else
    print_warning "PostgreSQL not detected. Please install PostgreSQL first:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install postgresql postgresql-contrib"
    echo "  macOS: brew install postgresql"
    echo "  Windows: Download from https://www.postgresql.org/download/"
    echo ""
    print_warning "You can still run the application, but data warehouse features will not work."
    echo "Run 'python3 setup_database.py' after installing PostgreSQL."
fi

print_success "Backend setup complete!"

# Setup Frontend
print_status "Setting up Angular frontend..."

cd frontend

# Install Node.js dependencies
print_status "Installing Node.js dependencies..."
npm install

print_success "Frontend setup complete!"

# Go back to root
cd ..

# Check if tmux is available for running both servers
if command -v tmux &> /dev/null; then
    print_status "tmux detected. Starting both servers in tmux session..."
    
    # Kill existing session if it exists
    tmux kill-session -t excel-generator 2>/dev/null || true
    
    # Create new session
    tmux new-session -d -s excel-generator
    
    # Split window
    tmux split-window -h -t excel-generator
    
    # Start backend in left pane
    tmux send-keys -t excel-generator:0.0 "cd $(pwd) && source venv/bin/activate && cd app && python main.py" Enter
    
    # Start frontend in right pane
    tmux send-keys -t excel-generator:0.1 "cd $(pwd)/frontend && npm start" Enter
    
    print_success "Both servers are starting in tmux session 'excel-generator'"
    echo ""
    echo "🌐 Backend: http://localhost:8000"
    echo "🎨 Frontend: http://localhost:4200"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo ""
    echo "📱 To view the session: tmux attach -t excel-generator"
    echo "💡 To detach: Press Ctrl+B, then D"
    echo "🚪 To stop: Press Ctrl+C in each pane, or run: tmux kill-session -t excel-generator"
    
    # Wait a moment then attach
    sleep 3
    tmux attach-session -t excel-generator
    
else
    print_warning "tmux not available. You'll need to start servers manually in separate terminals."
    echo ""
    echo "Terminal 1 (Backend):"
    echo "  cd $(pwd)"
    echo "  source venv/bin/activate"
    echo "  cd app"
    echo "  python main.py"
    echo ""
    echo "Terminal 2 (Frontend):"
    echo "  cd $(pwd)/frontend"
    echo "  npm start"
    echo ""
    echo "🌐 Backend will be at: http://localhost:8000"
    echo "🎨 Frontend will be at: http://localhost:4200"
fi

print_success "Setup complete! 🎉" 