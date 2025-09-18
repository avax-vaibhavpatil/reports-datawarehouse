gut#!/bin/bash

# Start Both Backend and Frontend Servers
echo "🚀 Starting Excel Generator - Full Stack Application..."

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "❌ Error: tmux is not installed. Please install tmux first:"
    echo "   Ubuntu/Debian: sudo apt install tmux"
    echo "   macOS: brew install tmux"
    echo "   Or run the individual scripts:"
    echo "   - ./start_backend.sh (in one terminal)"
    echo "   - ./start_frontend.sh (in another terminal)"
    exit 1
fi

# Create a new tmux session
echo "📱 Creating tmux session..."
tmux new-session -d -s excel-generator

# Split the window horizontally
tmux split-window -h -t excel-generator

# Start backend in the left pane
echo "🔧 Starting backend in left pane..."
tmux send-keys -t excel-generator:0.0 "cd $(pwd) && ./start_backend.sh" Enter

# Start frontend in the right pane
echo "🎨 Starting frontend in right pane..."
tmux send-keys -t excel-generator:0.1 "cd $(pwd) && ./start_frontend.sh" Enter

# Attach to the session
echo "✅ Both servers are starting..."
echo "🌐 Backend will be available at: http://localhost:8000"
echo "🎨 Frontend will be available at: http://localhost:4200"
echo ""
echo "📱 Attaching to tmux session..."
echo "💡 Use Ctrl+B then D to detach from the session"
echo "💡 Use 'tmux attach -t excel-generator' to reattach"
echo ""

sleep 3
tmux attach-session -t excel-generator 