#!/bin/bash
# Fix deployment issues on DigitalOcean server

SERVER_IP="165.22.55.118"
SSH_PASSWORD="weckL@071071W"

echo "Fixing deployment issues..."

sshpass -p "$SSH_PASSWORD" ssh -o StrictHostKeyChecking=no root@$SERVER_IP 'bash -s' << 'REMOTEFIX'
#!/bin/bash

cd /root/institutional-footprint

# 1. Install Node.js 20 if missing
if ! command -v node &> /dev/null || [[ $(node --version) != v20* ]]; then
    echo "Installing Node.js 20..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - > /dev/null 2>&1
    apt-get install -y nodejs > /dev/null 2>&1
fi

# 2. Ensure python-dotenv is installed
pip3 install --break-system-packages python-dotenv > /dev/null 2>&1

# 3. Rebuild dashboard
echo "Rebuilding dashboard..."
cd web-dashboard
rm -rf node_modules .next
npm install > /tmp/npm-install.log 2>&1
npm run build > /tmp/npm-build.log 2>&1

# 4. Start backend
echo "Starting backend..."
cd /root/institutional-footprint
pkill -f "python3 server.py" 2>/dev/null || true
sleep 1
nohup python3 server.py > logs/backend.log 2>&1 &
echo $! > server.pid
sleep 3

# 5. Start dashboard  
echo "Starting dashboard..."
cd web-dashboard
pkill -f "npm start" 2>/dev/null || true
sleep 1
PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
echo $! > ../dashboard.pid
sleep 4

# 6. Verify
echo ""
echo "=== Verification ==="
echo "Backend:"
curl -s http://localhost:8000/health 2>/dev/null || echo "Failed"

echo ""
echo "Dashboard:"
curl -s http://localhost:3001 2>/dev/null | grep -o "INSTITUTIONAL FOOTPRINT" | head -1 || echo "Failed"

echo ""
echo "Telegram:"
curl -s http://localhost:8000/telegram/status 2>/dev/null || echo "Failed"

echo ""
echo "✅ Fix complete!"
REMOTEFIX

echo ""
echo "Deployment fixed! Access at:"
echo "  http://$SERVER_IP:3001"
echo "  http://$SERVER_IP:8000"
