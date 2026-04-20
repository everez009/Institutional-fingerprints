# Pre-Deployment Checklist for DigitalOcean

## Before Running deploy-simple.sh

### 1. Verify Server Access

```bash
ssh root@165.22.55.118
```

If you can't connect, check:
- Server is running in DigitalOcean dashboard
- SSH key or password is correct
- Firewall allows port 22

### 2. Check Server Requirements

Once connected, verify:

```bash
# Check Python
python3 --version
pip3 --version

# Check Node.js (will be auto-installed if missing)
node --version
npm --version

# Check available memory
free -h

# Check disk space
df -h
```

**Minimum Requirements:**
- Python 3.8+
- 1GB RAM (2GB recommended)
- 5GB free disk space

### 3. Install Node.js Manually (If Auto-Install Fails)

If the deployment script fails to install Node.js:

```bash
# On the server
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Verify
node --version  # Should show v18.x.x
npm --version   # Should show 9.x.x or higher
```

### 4. Upload .env File with Telegram Credentials

From your Mac:

```bash
scp /Users/mac/institutional-footprint/.env root@165.22.55.118:/root/institutional-footprint/
```

Or manually create on server:

```bash
ssh root@165.22.55.118
nano /root/institutional-footprint/.env
```

Add:
```env
TELEGRAM_BOT_TOKEN=8770521964:AAER6wcXOntdGaF2tLQErsRk_i79YRXpLcM
TELEGRAM_CHAT_ID=883957377
SYMBOL=BTCUSDT
HOST=0.0.0.0
PORT=8000
```

### 5. Open Required Ports

In DigitalOcean Control Panel:
1. Go to Networking → Firewalls
2. Add rules:
   - Port 8000/tcp (Backend API)
   - Port 3001/tcp (Dashboard)
   - Port 22/tcp (SSH)

Or on server:

```bash
ufw allow 8000/tcp
ufw allow 3001/tcp
ufw allow 22/tcp
ufw enable
```

---

## Deployment Steps

### Step 1: Run Deployment Script

From your Mac:

```bash
cd /Users/mac/institutional-footprint
./deploy-simple.sh
```

Enter your SSH password when prompted.

### Step 2: Wait for Completion

The script will:
1. ✅ Pull code from GitHub
2. ✅ Install Python dependencies
3. ✅ Install Node.js (if needed)
4. ✅ Build dashboard
5. ✅ Start backend and dashboard
6. ✅ Verify everything is running

This takes 3-5 minutes.

### Step 3: Verify Deployment

After script completes, test:

```bash
# From your browser
http://165.22.55.118:8000/health
http://165.22.55.118:3001

# Or via curl
curl http://165.22.55.118:8000/health
curl http://165.22.55.118:3001 | grep "INSTITUTIONAL"
```

### Step 4: Test Telegram

```bash
curl -X POST http://165.22.55.118:8000/telegram/test
```

You should receive a message on Telegram.

---

## Troubleshooting Common Issues

### Issue 1: "npm: command not found"

**Solution:**
```bash
ssh root@165.22.55.118
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs
```

Then re-run deployment script.

### Issue 2: "pip3 killed" or Out of Memory

**Cause:** Server has less than 1GB RAM

**Solutions:**

**Option A: Add Swap Space**
```bash
# On server
fallocate -l 2G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

**Option B: Upgrade Droplet**
- Go to DigitalOcean dashboard
- Resize droplet to 2GB RAM ($12/month)

**Option C: Install Dependencies Individually**
```bash
pip3 install --break-system-packages python-dotenv
pip3 install --break-system-packages aiohttp
pip3 install --break-system-packages websockets
pip3 install --break-system-packages fastapi
pip3 install --break-system-packages uvicorn
```

### Issue 3: Backend Won't Start

Check logs:
```bash
ssh root@165.22.55.118
tail -50 /root/institutional-footprint/logs/backend.log
tail -50 /root/institutional-footprint/logs/backend-error.log
```

Common fixes:
```bash
# Check if port is in use
lsof -i :8000
kill -9 <PID>

# Restart
cd /root/institutional-footprint
./start-all.sh restart
```

### Issue 4: Dashboard Shows Blank Page

Check dashboard logs:
```bash
tail -50 /root/institutional-footprint/logs/dashboard.log
tail -50 /root/institutional-footprint/logs/dashboard-error.log
```

Rebuild dashboard:
```bash
cd /root/institutional-footprint/web-dashboard
npm run build
./start-all.sh restart
```

### Issue 5: Can't Access from Browser

Check firewall:
```bash
# On server
ufw status
ufw allow 8000/tcp
ufw allow 3001/tcp
```

Check if services are running:
```bash
ps aux | grep python
ps aux | grep node
```

---

## Manual Deployment (If Script Fails)

If the automated script doesn't work, deploy manually:

```bash
# SSH to server
ssh root@165.22.55.118

# Navigate to project
cd /root/institutional-footprint

# Pull latest code
git pull origin main

# Install Python dependencies one by one
pip3 install --break-system-packages python-dotenv
pip3 install --break-system-packages aiohttp
pip3 install --break-system-packages websockets
pip3 install --break-system-packages fastapi
pip3 install --break-system-packages uvicorn

# Install Node.js if needed
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Build dashboard
cd web-dashboard
npm install
npm run build
cd ..

# Start services
./start-all.sh start

# Verify
curl http://localhost:8000/health
curl http://localhost:3001 | grep "INSTITUTIONAL"
```

---

## Post-Deployment Verification

Run these checks after deployment:

```bash
# 1. Check backend health
curl http://165.22.55.118:8000/health

# Expected: {"status":"healthy",...}

# 2. Check dashboard loads
curl http://165.22.55.118:3001 | grep "INSTITUTIONAL FOOTPRINT"

# Expected: Should return HTML with title

# 3. Check Telegram configuration
curl http://165.22.55.118:8000/telegram/status

# Expected: {"configured":true,...}

# 4. Send test notification
curl -X POST http://165.22.55.118:8000/telegram/test

# Expected: Check your Telegram app

# 5. Check multi-symbol endpoint
curl http://165.22.55.118:8000/multi/summary | python3 -m json.tool

# Expected: JSON with BTC, ETH, PAXG, XAU data
```

---

## Monitoring After Deployment

### Check Logs Remotely

```bash
# Backend logs
ssh root@165.22.55.118 "tail -f /root/institutional-footprint/logs/backend.log"

# Dashboard logs
ssh root@165.22.55.118 "tail -f /root/institutional-footprint/logs/dashboard.log"
```

### Monitor System Resources

```bash
ssh root@165.22.55.118
htop  # or top
df -h  # disk usage
free -h  # memory usage
```

### Set Up Auto-Restart

```bash
# Copy systemd service file
scp institutional-footprint.service root@165.22.55.118:/etc/systemd/system/

# Enable on server
ssh root@165.22.55.118
systemctl daemon-reload
systemctl enable institutional-footprint
systemctl start institutional-footprint
systemctl status institutional-footprint
```

---

## Quick Reference

**Server IP:** 165.22.55.118  
**Backend:** http://165.22.55.118:8000  
**Dashboard:** http://165.22.55.118:3001  
**Multi-Symbol:** http://165.22.55.118:3001/multi  

**Deploy Command:**
```bash
cd /Users/mac/institutional-footprint && ./deploy-simple.sh
```

**SSH Access:**
```bash
ssh root@165.22.55.118
```

---

## Need Help?

1. Check this guide's troubleshooting section
2. Review logs: `tail -f logs/backend.log`
3. Verify server resources: `free -h && df -h`
4. Test endpoints individually
5. Check DigitalOcean dashboard for server status

Good luck with your deployment! 🚀
