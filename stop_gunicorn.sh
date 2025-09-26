#!/bin/bash

# Stop Gunicorn processes script
echo "🛑 Stopping Gunicorn processes..."

# Check if any Gunicorn processes are running
if pgrep -f gunicorn > /dev/null; then
    echo "📋 Found running Gunicorn processes:"
    ps aux | grep gunicorn | grep -v grep
    
    echo ""
    echo "🔪 Killing all Gunicorn processes..."
    pkill -f gunicorn
    
    # Wait a moment for graceful shutdown
    sleep 2
    
    # Force kill if still running
    if pgrep -f gunicorn > /dev/null; then
        echo "⚡ Force killing remaining processes..."
        pkill -9 -f gunicorn
    fi
    
    echo "✅ All Gunicorn processes stopped"
else
    echo "ℹ️  No Gunicorn processes found running"
fi

# Remove PID file if it exists
if [ -f "/tmp/gunicorn.pid" ]; then
    echo "🗑️  Removing stale PID file..."
    rm -f /tmp/gunicorn.pid
fi

echo "🎉 Cleanup complete!"