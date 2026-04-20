#!/bin/bash
# Deploy Institutional Footprint to DigitalOcean

SERVER_IP="165.22.55.118"
REMOTE_DIR="/root/institutional-footprint"
PROJECT_NAME="institutional-footprint"

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   Deploying to DigitalOcean                           ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Step 1: Create deployment archive
echo "📦 Creating deployment archive..."
cd /Users/mac/institutional-footprint

# Create tarball excluding unnecessary files
tar czf /tmp/${PROJECT_NAME}.tar.gz \
    --exclude='.git' \
    --exclude='node_modules' \
    --exclude='.next' \
    --exclude='logs' \
    --exclude='*.pid' \
    --exclude='.env' \
    .

echo "✅ Archive created"
echo ""

# Step 2: Upload to server
echo "📤 Uploading to DigitalOcean ($SERVER_IP)..."
scp /tmp/${PROJECT_NAME}.tar.gz root@${SERVER_IP}:/tmp/

if [ $? -ne 0 ]; then
    echo "❌ Upload failed. Check SSH connection."
    exit 1
fi

echo "✅ Upload complete"
echo ""

# Step 3: Deploy on server
echo "🚀 Deploying on server..."
ssh root@${SERVER_IP} << 'REMOTE_SCRIPT'
#!/bin/bash

PROJECT_DIR="/root/institutional-footprint"

# Create directory if not exists
mkdir -p $PROJECT_DIR

# Extract archive
cd $PROJECT_DIR
tar xzf /tmp/${PROJECT_NAME}.tar.gz

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --break-system-packages -r requirements.txt

# Install Node.js dependencies for dashboard
echo "Installing dashboard dependencies..."
cd web-dashboard
npm install
npm run build

# Create .env file if not exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << 'ENVFILE'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Trading Symbol
SYMBOL=BTCUSDT

# Server Configuration
HOST=0.0.0.0
PORT=8000
ENVFILE
    echo "⚠️  Please update .env with your Telegram credentials"
fi

# Stop existing processes
echo "Stopping existing services..."
pkill -f "python3 server.py" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
sleep 2

# Start backend
echo "Starting backend server..."
cd $PROJECT_DIR
nohup python3 server.py > logs/backend.log 2>&1 &
echo $! > server.pid
sleep 3

# Start dashboard
echo "Starting web dashboard..."
cd web-dashboard
PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
echo $! > ../dashboard.pid
sleep 3

# Verify services
echo ""
echo "Verifying deployment..."
sleep 2

BACKEND_STATUS=$(curl -s http://localhost:8000/health | grep -o '"status":"healthy"' || echo "failed")
DASHBOARD_STATUS=$(curl -s http://localhost:3001 | grep -o "INSTITUTIONAL FOOTPRINT" || echo "failed")

if [ "$BACKEND_STATUS" = '"status":"healthy"' ]; then
    echo "✅ Backend is running"
else
    echo "❌ Backend failed to start"
fi

if [ "$DASHBOARD_STATUS" = "INSTITUTIONAL FOOTPRINT" ]; then
    echo "✅ Dashboard is running"
else
    echo "❌ Dashboard failed to start"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "Deployment Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Access URLs:"
echo "  Backend API: http://${SERVER_IP}:8000"
echo "  Dashboard: http://${SERVER_IP}:3001"
echo ""
echo "Management commands:"
echo "  View logs: tail -f /root/institutional-footprint/logs/backend.log"
echo "  Restart: cd /root/institutional-footprint && ./start-all.sh restart"
echo ""

REMOTE_SCRIPT

# Cleanup
rm -f /tmp/${PROJECT_NAME}.tar.gz

echo ""
echo "✅ Deployment script completed!"
