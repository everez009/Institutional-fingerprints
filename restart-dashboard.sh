#!/bin/bash
sshpass -p 'weckL@071071W' ssh -o StrictHostKeyChecking=no root@165.22.55.118 << 'EOF'
cd /root/institutional-footprint/web-dashboard
pkill -f "npm" 2>/dev/null || true
sleep 2
PORT=3001 nohup npm run dev > ../logs/dashboard.log 2>&1 &
echo $! > ../dashboard.pid
EOF
echo "Dashboard restarting... waiting 12 seconds"
sleep 12
echo "Checking if dashboard is up..."
curl -s http://165.22.55.118:3001 | head -c 200
echo ""
echo "---"
echo "Checking logs..."
sshpass -p 'weckL@071071W' ssh -o StrictHostKeyChecking=no root@165.22.55.118 "tail -15 /root/institutional-footprint/logs/dashboard.log"
