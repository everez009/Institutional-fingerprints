#!/bin/bash
sshpass -p 'weckL@071071W' ssh -o StrictHostKeyChecking=no root@165.22.55.118 << 'EOF'
cd /root/institutional-footprint
pkill -f "python3 server.py" 2>/dev/null || true
sleep 2
nohup python3 server.py > logs/backend.log 2>&1 &
echo $! > server.pid
EOF
echo "Server restart command sent. Waiting 10 seconds..."
sleep 10
echo "Testing backend..."
curl -s http://165.22.55.118:8000/health | python3 -m json.tool
echo ""
echo "Testing state endpoint..."
curl -s http://165.22.55.118:8000/state | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Price: ${d.get(\"price\", 0):,.2f}')"
