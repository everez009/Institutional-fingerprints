# DigitalOcean Deployment Guide

## Quick Deploy (Recommended)

### Option 1: Using the Deployment Script

```bash
cd /Users/mac/institutional-footprint
./deploy-do.sh
```

You'll be prompted for your SSH password. Enter it when asked.

### Option 2: Manual Deployment

If the script doesn't work, follow these steps:

---

## Step-by-Step Manual Deployment

### 1. Connect to Your Server

```bash
ssh root@165.22.55.118
```

Enter your password when prompted.

### 2. Create Project Directory

```bash
mkdir -p /root/institutional-footprint
cd /root/institutional-footprint
```

### 3. Clone or Upload Code

**Option A: Clone from GitHub** (Easiest)
```bash
git clone https://github.com/everez009/Institutional-fingerprints.git .
```

**Option B: Upload via SCP** (From your Mac)
```bash
# On your Mac, run this:
cd /Users/mac/institutional-footprint
tar czf /tmp/deploy.tar.gz --exclude='.git' --exclude='node_modules' --exclude='.next' --exclude='logs' .
scp /tmp/deploy.tar.gz root@165.22.55.118:/root/institutional-footprint/

# Then on the server:
cd /root/institutional-footprint
tar xzf deploy.tar.gz
rm deploy.tar.gz
```

### 4. Install Dependencies

```bash
# Install Python dependencies
pip3 install --break-system-packages -r requirements.txt

# Install Node.js dependencies
cd web-dashboard
npm install
npm run build
cd ..
```

### 5. Configure Environment

```bash
nano .env
```

Add your configuration:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SYMBOL=BTCUSDT
HOST=0.0.0.0
PORT=8000
```

Save with Ctrl+O, Enter, Ctrl+X

### 6. Start Services

```bash
# Make start script executable
chmod +x start-all.sh

# Start everything
./start-all.sh start
```

### 7. Verify Deployment

```bash
# Check backend
curl http://localhost:8000/health

# Check dashboard
curl http://localhost:3001 | grep "INSTITUTIONAL FOOTPRINT"

# View logs
tail -f logs/backend.log
```

---

## Access Your Deployment

Once deployed, access your system at:

- **Backend API**: http://165.22.55.118:8000
- **Web Dashboard**: http://165.22.55.118:3001
- **Multi-Symbol View**: http://165.22.55.118:3001/multi

---

## Firewall Configuration

Make sure ports are open on DigitalOcean:

1. Go to DigitalOcean Control Panel
2. Navigate to Networking → Firewalls
3. Add rules:
   - Port 8000 (Backend API)
   - Port 3001 (Dashboard)
   - Port 22 (SSH)

Or via command line on the server:
```bash
ufw allow 8000/tcp
ufw allow 3001/tcp
ufw reload
```

---

## Auto-Start on Boot

To ensure the system starts automatically after server reboot:

### Option 1: Using systemd (Recommended)

Create service file:
```bash
nano /etc/systemd/system/institutional-footprint.service
```

Add:
```ini
[Unit]
Description=Institutional Footprint Detection System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/institutional-footprint
ExecStart=/bin/bash /root/institutional-footprint/start-all.sh start
ExecStop=/bin/bash /root/institutional-footprint/start-all.sh stop
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
systemctl daemon-reload
systemctl enable institutional-footprint
systemctl start institutional-footprint
systemctl status institutional-footprint
```

### Option 2: Using crontab

```bash
crontab -e
```

Add:
```cron
@reboot cd /root/institutional-footprint && ./start-all.sh start
```

---

## Management Commands

### View Status
```bash
./start-all.sh status
```

### Restart Services
```bash
./start-all.sh restart
```

### View Logs
```bash
# Backend logs
tail -f logs/backend.log

# Dashboard logs
tail -f logs/dashboard.log

# Errors only
tail -f logs/backend-error.log
```

### Stop Services
```bash
./start-all.sh stop
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000
lsof -i :3001

# Kill process
kill -9 <PID>

# Restart
./start-all.sh restart
```

### No Data Showing
```bash
# Check WebSocket connection
tail -f logs/backend.log | grep ENGINE

# Verify Binance connectivity
ping stream.binance.com
```

### High Memory Usage
```bash
# Check memory
free -h

# Restart if needed
./start-all.sh restart
```

### Telegram Not Working
```bash
# Check configuration
curl http://localhost:8000/telegram/status

# Test notification
curl -X POST http://localhost:8000/telegram/test
```

---

## Security Recommendations

1. **Change SSH Port** (Optional but recommended)
2. **Set up SSH Keys** instead of password
3. **Enable UFW Firewall**
4. **Use HTTPS** with nginx reverse proxy (for production)
5. **Regular Updates**: `apt update && apt upgrade`

---

## Monitoring

### Check System Resources
```bash
# CPU and Memory
top

# Disk usage
df -h

# Process list
ps aux | grep python
ps aux | grep node
```

### Set Up Log Rotation
```bash
nano /etc/logrotate.d/institutional-footprint
```

Add:
```
/root/institutional-footprint/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

---

## Update Deployment

To update with latest code:

```bash
# On the server
cd /root/institutional-footprint

# Pull latest changes
git pull origin main

# Or upload new code via SCP from your Mac

# Install any new dependencies
pip3 install --break-system-packages -r requirements.txt
cd web-dashboard && npm install && npm run build && cd ..

# Restart services
./start-all.sh restart
```

---

## Backup

Backup your configuration:
```bash
# Backup .env file
cp .env .env.backup

# Backup to your Mac
scp root@165.22.55.118:/root/institutional-footprint/.env ~/backups/
```

---

## Support

If you encounter issues:

1. Check logs: `tail -f logs/backend.log`
2. Verify services: `./start-all.sh status`
3. Test endpoints: `curl http://localhost:8000/health`
4. Review this guide's troubleshooting section

---

## Cost Estimate

DigitalOcean Droplet (recommended specs):
- **Basic**: $6/month (1GB RAM, 1 CPU) - Minimum
- **Standard**: $12/month (2GB RAM, 1 CPU) - Recommended
- **Premium**: $18/month (2GB RAM, 2 CPU) - For heavy usage

Your current server (165.22.55.118) should work fine!
