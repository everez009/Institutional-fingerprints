#!/bin/bash
# Simple DigitalOcean Deployment Script

SERVER_IP="165.22.55.118"
PROJECT_DIR="/root/institutional-footprint"

echo "╔══════════════════════════════════════════════╗"
echo "║  Institutional Footprint - DO Deploy        ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "Server: $SERVER_IP"
echo ""

# Step 1: SSH and deploy
echo "Connecting to server..."
echo "You'll be prompted for your SSH password."
echo ""

ssh root@${SERVER_IP} << ENDSSH
#!/bin/bash

echo "=========================================="
echo "Starting Deployment..."
echo "=========================================="

PROJECT_DIR="/root/institutional-footprint"

# Create directory
mkdir -p \$PROJECT_DIR
cd \$PROJECT_DIR

# Pull latest code from GitHub
echo ""
echo "📥 Pulling latest code from GitHub..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/everez009/Institutional-fingerprints.git .
    mv Institutional-fingerprints/* . 2>/dev/null || true
    mv Institutional-fingerprints/.* . 2>/dev/null || true
    rm -rf Institutional-fingerprints
fi

# Check if Python dependencies need updating
echo ""
echo "📦 Checking Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install --break-system-packages python-dotenv aiohttp websockets fastapi uvicorn 2>&1 | tail -3
    echo "✅ Python dependencies updated"
else
    echo "❌ pip3 not found! Installing Python packages manually..."
    apt-get update && apt-get install -y python3-pip
    pip3 install --break-system-packages -r requirements.txt
fi

# Check if Node.js is installed
echo ""
echo "📦 Checking Node.js..."
if ! command -v npm &> /dev/null; then
    echo "Node.js not found. Installing..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y nodejs
    echo "✅ Node.js installed"
else
    echo "✅ Node.js already installed (\$(node --version))"
fi

# Install Node.js dependencies
echo ""
echo "📦 Installing dashboard dependencies..."
cd web-dashboard
npm install 2>&1 | tail -5
npm run build 2>&1 | tail -5
cd ..

# Create logs directory
mkdir -p logs

# Stop existing services
echo ""
echo "⏹️  Stopping existing services..."
pkill -f "python3 server.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
sleep 2

# Start backend
echo ""
echo "🚀 Starting backend server..."
nohup python3 server.py > logs/backend.log 2>&1 &
echo \$! > server.pid
sleep 4

# Start dashboard
echo "🚀 Starting web dashboard..."
cd web-dashboard
PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
echo \$! > ../dashboard.pid
cd ..
sleep 4

# Verify
echo ""
echo "=========================================="
echo "Verifying Deployment..."
echo "=========================================="
sleep 2

BACKEND_CHECK=\$(curl -s http://localhost:8000/health 2>/dev/null)
DASHBOARD_CHECK=\$(curl -s http://localhost:3001 2>/dev/null | head -1)

if echo "\$BACKEND_CHECK" | grep -q "healthy"; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend failed to start"
    echo "Check logs: tail -f logs/backend.log"
    echo "Last 10 lines:"
    tail -10 logs/backend.log
fi

if echo "\$DASHBOARD_CHECK" | grep -q "INSTITUTIONAL"; then
    echo "✅ Dashboard is running on port 3001"
else
    echo "❌ Dashboard failed to start"
    echo "Check logs: tail -f logs/dashboard.log"
    echo "Last 10 lines:"
    tail -10 logs/dashboard.log
fi

echo ""
echo "=========================================="
echo "✅ DEPLOYMENT COMPLETE!"
echo "=========================================="
echo ""
echo "Access your system:"
echo "  📊 Dashboard: http://${SERVER_IP}:3001"
echo "  🔌 API: http://${SERVER_IP}:8000"
echo "  📈 Multi-Symbol: http://${SERVER_IP}:3001/multi"
echo ""
echo "Management:"
echo "  Status: ./start-all.sh status"
echo "  Logs: tail -f logs/backend.log"
echo "  Restart: ./start-all.sh restart"
echo ""
echo "Telegram configured: ✅"
echo ""

ENDSSH

echo ""
echo "Deployment script finished!"
echo "If you see errors above, check your SSH connection."
