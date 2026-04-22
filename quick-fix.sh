#!/bin/bash
sshpass -p 'weckL@071071W' ssh -o StrictHostKeyChecking=no root@165.22.55.118 << 'EOF'
cd /root/institutional-footprint
pip3 install --break-system-packages --ignore-installed fastapi uvicorn python-dotenv aiohttp websockets
cd web-dashboard && npm run build
pkill -f "python3 server.py" || true
pkill -f "next start" || true
sleep 2
cd /root/institutional-footprint
nohup python3 server.py > logs/backend.log 2>&1 &
echo $! > server.pid
cd web-dashboard
PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
echo $! > ../dashboard.pid
sleep 5
curl -s http://localhost:8000/health && echo "" && curl -s http://localhost:3001 | grep -o "INSTITUTIONAL FOOTPRINT"
EOF
