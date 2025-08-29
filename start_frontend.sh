#!/bin/bash

# Start Angular Frontend Development Server
echo "🎨 Starting Excel Generator Frontend..."

# Check if we're in the right directory
if [ ! -d "frontend" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Start the development server
echo "🌐 Starting Angular dev server on http://localhost:4200"
echo "📱 The app will automatically reload when you make changes"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start 