#!/bin/bash
# Setup script for local testing of Institutional Footprint System

echo "=========================================="
echo "Institutional Footprint - Local Setup"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (required for signals)"
    echo "   - TELEGRAM_BOT_TOKEN (optional, for notifications)"
    echo "   - TELEGRAM_CHAT_ID (optional, for notifications)"
    echo ""
    read -p "Press Enter after you've updated .env..."
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  ./manage.sh start"
echo ""
echo "To check status:"
echo "  ./manage.sh status"
echo ""
echo "To view logs:"
echo "  ./manage.sh logs"
echo ""
echo "Server will run on: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "For frontend, you can:"
echo "  1. Use the provided App.jsx with a React setup"
echo "  2. Or test API endpoints directly via browser/curl"
echo ""
