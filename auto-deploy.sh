#!/bin/bash
# Automated Deployment with Password Authentication
# Uses sshpass to avoid interactive password prompts

SERVER_IP="165.22.55.118"
SSH_PASSWORD="weckL@071071W"
PROJECT_DIR="/root/institutional-footprint"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Auto-Deploy to DigitalOcean                    ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""

# Check if sshpass is installed
if ! command -v sshpass &> /dev/null; then
    echo "Installing sshpass..."
    brew install sshpass 2>&1 | tail -3
fi

# Step 1: Upload .env file
echo "📤 Uploading .env file with Telegram credentials..."
sshpass -p "${SSH_PASSWORD}" scp -o StrictHostKeyChecking=no \
    /Users/mac/institutional-footprint/.env \
    root@${SERVER_IP}:${PROJECT_DIR}/.env

if [ $? -eq 0 ]; then
    echo "✅ .env file uploaded"
else
    echo "❌ Failed to upload .env file"
    exit 1
fi

echo ""

# Step 2: Run deployment on server
echo "🚀 Starting remote deployment..."
echo ""

sshpass -p "${SSH_PASSWORD}" ssh -o StrictHostKeyChecking=no root@${SERVER_IP} << 'ENDSSH'
#!/bin/bash

PROJECT_DIR="/root/institutional-footprint"

echo "=========================================="
echo "Starting Automated Deployment"
echo "=========================================="

# Create directory
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Pull latest code from GitHub
echo ""
echo "📥 Pulling latest code from GitHub..."
if [ -d ".git" ]; then
    git pull origin main
else
    git clone https://github.com/everez009/Institutional-fingerprints.git temp_clone
    cp -r temp_clone/* .
    cp -r temp_clone/.* . 2>/dev/null || true
    rm -rf temp_clone
fi

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages python-dotenv aiohttp websockets fastapi uvicorn 2>&1 | tail -5
echo "✅ Python dependencies installed"

# Check and install Node.js
echo ""
echo "📦 Checking Node.js..."
if ! command -v npm &> /dev/null; then
    echo "Installing Node.js..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - > /dev/null 2>&1
    apt-get install -y nodejs > /dev/null 2>&1
    echo "✅ Node.js installed"
else
    echo "✅ Node.js already installed ($(node --version))"
fi

# Install dashboard dependencies
echo ""
echo "📦 Building dashboard..."
cd web-dashboard
npm install > /dev/null 2>&1
npm run build > /dev/null 2>&1
cd ..
echo "✅ Dashboard built"

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
echo $! > server.pid
sleep 4

# Start dashboard
echo "🚀 Starting web dashboard..."
cd web-dashboard
PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
echo $! > ../dashboard.pid
cd ..
sleep 4

# Verify deployment
echo ""
echo "=========================================="
echo "Verifying Deployment..."
echo "=========================================="

BACKEND_CHECK=$(curl -s http://localhost:8000/health 2>/dev/null)
DASHBOARD_CHECK=$(curl -s http://localhost:3001 2>/dev/null | head -1)

if echo "$BACKEND_CHECK" | grep -q "healthy"; then
    echo "✅ Backend is running on port 8000"
else
    echo "❌ Backend failed to start"
    echo "Last 10 log lines:"
    tail -10 logs/backend.log
fi

if echo "$DASHBOARD_CHECK" | grep -q "INSTITUTIONAL"; then
    echo "✅ Dashboard is running on port 3001"
else
    echo "❌ Dashboard failed to start"
    echo "Last 10 log lines:"
    tail -10 logs/dashboard.log
fi

# Test Telegram
echo ""
echo "📱 Testing Telegram..."
TELEGRAM_TEST=$(curl -s -X POST http://localhost:8000/telegram/test 2>/dev/null)
if echo "$TELEGRAM_TEST" | grep -q "success"; then
    echo "✅ Telegram notification sent successfully!"
else
    echo "⚠️  Telegram test failed (check .env file)"
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

ENDSSH

echo ""
echo "✅ Automated deployment finished!"
echo ""
echo "You can now access:"
echo "  http://${SERVER_IP}:3001"
echo ""
