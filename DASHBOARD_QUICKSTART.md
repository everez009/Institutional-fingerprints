# Web Dashboard - Quick Start Guide

## ✅ System Status

Your Institutional Footprint Detection System is now running with a complete web dashboard!

### Current Services
- ✅ **Backend API**: Running on http://localhost:8000
- ✅ **Web Dashboard**: Running on http://localhost:3001
- ✅ **Auto-restart**: Configured for 24/7 operation

---

## 🌐 Access Your Dashboard

Open your browser and navigate to:
**http://localhost:3001**

### Dashboard Features

1. **Real-time Market Metrics**
   - Current price
   - Live delta
   - Cumulative delta
   - Spoof activity counter

2. **Delta History Chart**
   - Visual representation of order flow
   - Real-time updates every 3 seconds

3. **Order Book DOM**
   - Top 10 bids and asks
   - Visual depth indicators
   - Color-coded buy/sell walls

4. **Current Signal Display**
   - Signal direction (LONG/SHORT/MONITOR)
   - Conviction level (HIGH/MEDIUM/LOW)
   - Score bar visualization
   - Entry, stop loss, and take profit levels
   - Risk-reward ratio
   - Institutional narrative

5. **Market Phase Tracker**
   - Accumulation
   - Stop Hunt
   - Entry Confirmed
   - Markup

6. **Fingerprint Detection Panel**
   - Absorption detection
   - Iceberg orders
   - Stop hunts
   - Delta divergence
   - Real-time status indicators

7. **Signal History**
   - Last 20 signals
   - Color-coded by direction
   - Opacity-based age indication
   - Primary reasons displayed

---

## 🔄 24/7 Operation

### Option 1: Use start-all.sh Script (Recommended)

```bash
# Start both backend and dashboard
./start-all.sh start

# Check status
./start-all.sh status

# Restart everything
./start-all.sh restart

# Stop all services
./start-all.sh stop

# View logs
./start-all.sh logs           # Backend logs
./start-all.sh dashboard-logs # Dashboard logs
./start-all.sh errors         # Error logs
```

### Option 2: Auto-start on Boot (macOS)

Install the launchd service for automatic startup:

```bash
# Copy plist to LaunchAgents
cp com.institutional.footprint.plist ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/com.institutional.footprint.plist

# Verify it's loaded
launchctl list | grep institutional

# The system will now:
# - Start automatically on boot
# - Restart if it crashes
# - Run 24/7 in the background
```

To unload later:
```bash
launchctl unload ~/Library/LaunchAgents/com.institutional.footprint.plist
```

### Option 3: Linux Systemd (For Linux Servers)

Use the provided `institutional-footprint.service` file:

```bash
sudo cp institutional-footprint.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable institutional-footprint
sudo systemctl start institutional-footprint
```

---

## 📊 Monitoring

### Check System Health

```bash
# Backend health check
curl http://localhost:8000/health

# Force signal generation
curl -X POST http://localhost:8000/signal/force

# View current state
curl http://localhost:8000/state
```

### View Logs

```bash
# Backend logs
tail -f logs/backend.log

# Dashboard logs
tail -f logs/dashboard.log

# Error logs
tail -f logs/backend-error.log
tail -f logs/dashboard-error.log
```

---

## 🎨 Dashboard Customization

The dashboard is built with Next.js and React. To customize:

1. Edit `/web-dashboard/app/page.tsx`
2. Rebuild: `cd web-dashboard && npm run build`
3. Restart: `./start-all.sh restart`

---

## 🔧 Troubleshooting

### Dashboard Not Loading?

```bash
# Check if services are running
./start-all.sh status

# Check dashboard logs
tail -50 logs/dashboard-error.log

# Restart dashboard only
cd web-dashboard && npm run build && PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
```

### Backend Not Connecting?

```bash
# Check backend logs
tail -50 logs/backend-error.log

# Restart backend
./manage.sh restart
```

### Port Already in Use?

Edit the port in `start-all.sh`:
```bash
# Change this line:
PORT=3001 nohup npm start ...
```

---

## 📱 Mobile Access

To access the dashboard from other devices on your network:

1. Find your computer's IP address:
   ```bash
   ipconfig getifaddr en0  # macOS
   ```

2. Access from other device:
   ```
   http://YOUR_IP_ADDRESS:3001
   ```

---

## 🚀 Production Deployment

For production deployment, consider:

1. **Railway/Render**: Deploy backend as a service
2. **Vercel**: Deploy frontend dashboard
3. **VPS**: Full control with systemd
4. **Docker**: Containerize everything (coming soon)

---

## 📈 What You'll See

When institutional patterns are detected, the dashboard will show:

- **GREEN** signals for LONG opportunities
- **RED** signals for SHORT opportunities  
- **YELLOW** for MONITOR phase
- Real-time fingerprint detection
- Score-based conviction levels
- Complete trade setup with entry/stop/targets

---

## ✨ Key Benefits

✅ **No LLM Costs** - Rule-based detection  
✅ **Real-time Updates** - 3-second polling  
✅ **Beautiful UI** - Professional dark theme  
✅ **Mobile Responsive** - Works on all devices  
✅ **Auto-restart** - 24/7 reliability  
✅ **Easy Monitoring** - Comprehensive logging  

---

**Enjoy your institutional-grade trading dashboard!** 🎯
