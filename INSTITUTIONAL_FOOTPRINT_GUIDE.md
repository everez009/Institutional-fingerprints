# Institutional Footprint Detection System
## Complete User Guide

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Quick Start](#quick-start)
3. [Dashboard Guide](#dashboard-guide)
4. [Multi-Symbol Monitoring](#multi-symbol-monitoring)
5. [Signal Interpretation](#signal-interpretation)
6. [Telegram Notifications](#telegram-notifications)
7. [System Management](#system-management)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Configuration](#advanced-configuration)

---

## System Overview

### What It Does

The Institutional Footprint Detection System monitors cryptocurrency markets in real-time to identify institutional trading patterns:

- **Absorption Detection**: Identifies when large orders are being absorbed at key levels
- **Iceberg Orders**: Detects hidden large orders that refresh as they're filled
- **Stop Hunts**: Recognizes when price sweeps liquidity before reversing
- **Delta Divergence**: Spots discrepancies between price action and order flow
- **Spoof Detection**: Identifies fake orders placed to manipulate the market

### Key Features

✅ **Real-Time Monitoring** - Live WebSocket connections to Binance  
✅ **Multi-Symbol Support** - Monitor BTC, ETH, PAXG simultaneously  
✅ **Rule-Based Detection** - No LLM costs, transparent scoring system  
✅ **Telegram Alerts** - Instant notifications for high-conviction signals  
✅ **Web Dashboard** - Beautiful UI for visual analysis  
✅ **24/7 Operation** - Auto-restart on crashes or reboots  

### Architecture

```
┌─────────────────────────────────────────┐
│         Web Dashboard (Port 3001)       │
│  ┌──────────┐  ┌──────────┐            │
│  │ Single   │  │ Multi    │            │
│  │ Symbol   │  │ Symbol   │            │
│  └──────────┘  └──────────┘            │
└──────────────┬──────────────────────────┘
               │ HTTP Polling (3s)
┌──────────────▼──────────────────────────┐
│      FastAPI Backend (Port 8000)        │
│  ┌────────┐ ┌────────┐ ┌────────┐     │
│  │ BTC    │ │ ETH    │ │ PAXG   │     │
│  │Engine  │ │Engine  │ │Engine  │     │
│  └────────┘ └────────┘ └────────┘     │
└──────────────┬──────────────────────────┘
               │ WebSocket Streams
┌──────────────▼──────────────────────────┐
│         Binance Exchange                │
│  wss://stream.binance.com:9443/ws      │
└─────────────────────────────────────────┘
```

---

## Quick Start

### Prerequisites

- macOS or Linux system
- Python 3.10+
- Node.js 18+
- Internet connection

### Installation

The system is already installed and running. To verify:

```bash
cd /Users/mac/institutional-footprint
./start-all.sh status
```

### Access Dashboards

**Single Symbol View**: http://localhost:3001  
**Multi-Symbol View**: http://localhost:3001/multi  
**API Health Check**: http://localhost:8000/health

### Currently Monitored Symbols

- **BTCUSDT** - Bitcoin/USDT
- **ETHUSDT** - Ethereum/USDT
- **PAXGUSDT** - Pax Gold/USDT

---

## Dashboard Guide

### Single Symbol Dashboard (/)

The single symbol view provides detailed analysis for one asset at a time.

#### Header Section

- **Symbol Selector**: Dropdown to switch between monitored assets
- **Connection Status**: Green = Connected, Red = Disconnected
- **Last Update**: Shows when data was last refreshed
- **Multi-Symbol Button**: Switch to grid view

#### Key Metrics Cards

1. **Current Price** - Real-time asset price
2. **Delta** - Net buying/selling pressure (current candle)
3. **Cumulative Delta** - Running total of delta
4. **Spoofs (60s)** - Number of spoofed orders detected

#### Order Book DOM (Depth of Market)

Visual representation of bid/ask walls:
- **Green bars** = Buy orders (bids)
- **Red bars** = Sell orders (asks)
- Bar length = Order size
- Helps identify support/resistance levels

#### Current Signal Card

Displays the latest trading signal:
- **Signal Type**: LONG, SHORT, or MONITOR
- **Conviction Level**: HIGH, MEDIUM, or LOW
- **Score**: Numerical conviction score (-10 to +10)
- **Phase**: Current market phase detection

#### Fingerprint Detection

Shows active institutional patterns:
- ✅ **Absorption** - Large orders being absorbed
- ✅ **Iceberg** - Hidden large orders detected
- ✅ **Stop Hunt** - Liquidity sweep confirmed
- ✅ **Divergence** - Price/delta mismatch

#### Delta Chart

Historical delta visualization showing:
- Individual candle deltas (bars)
- Cumulative delta trend (line)
- Bullish (green) vs Bearish (red) pressure

#### Signal History

Table of recent signals with:
- Timestamp
- Signal type and conviction
- Entry price and stop loss
- Score breakdown

### Multi-Symbol Dashboard (/multi)

The multi-symbol view shows all assets simultaneously in a grid layout.

#### Grid Cards

Each card displays:
- **Symbol Name** - Asset being monitored
- **Current Price** - Real-time price
- **Signal Badge** - Color-coded signal type
- **Conviction Score** - Strength indicator
- **Key Metrics** - Delta, cumulative delta, spoofs
- **Fingerprint Indicators** - Active pattern dots

#### Color Coding

- 🟢 **Green** = LONG signal or bullish metrics
- 🔴 **Red** = SHORT signal or bearish metrics
- 🟡 **Yellow** = MONITOR signal or neutral
- ⚪ **Gray** = No signal or inactive

---

## Multi-Symbol Monitoring

### How It Works

The system runs independent engine instances for each symbol:

```python
# Each symbol has its own:
- WebSocket connection to Binance
- Order book tracking
- Trade processing
- Pattern detection
- Signal generation
```

### Benefits

✅ **Simultaneous Analysis** - No switching delays  
✅ **Independent Detection** - Each symbol analyzed separately  
✅ **Comprehensive View** - See all opportunities at once  
✅ **Efficient Monitoring** - One dashboard for multiple assets  

### Adding New Symbols

Edit `/Users/mac/institutional-footprint/server.py`:

```python
multi_engine = MultiSymbolEngine([
    "BTCUSDT", 
    "ETHUSDT", 
    "PAXGUSDT",
    "XAUUSDT"  # Add more symbols here
])
```

Supported symbols: BTCUSDT, ETHUSDT, PAXGUSDT, XAUUSDT

Restart the system after changes:

```bash
./start-all.sh restart
```

---

## Signal Interpretation

### Scoring System

The system uses a rule-based scoring algorithm (NO LLM):

| Pattern | Max Score | Description |
|---------|-----------|-------------|
| Absorption | +3 | Large orders absorbed at level |
| Iceberg | +2 | Hidden large order detected |
| Stop Hunt | +4 | Confirmed liquidity sweep |
| Delta Divergence | +2 | Price/delta mismatch |
| Volume Spike | +1 | 3x+ average volume |

### Signal Thresholds

- **MONITOR** (Score < 6): Watch for setup development
- **MEDIUM** (Score 6-8): Potential opportunity forming
- **HIGH** (Score 9+): Strong institutional activity detected

### Signal Types

#### LONG Signal

Generated when:
- Stop hunt confirmed with reclaim
- Bullish delta divergence
- Absorption at support
- Score ≥ 6

**Entry**: Current market price  
**Stop Loss**: Below swept low (0.2% buffer)  
**Target**: Based on risk/reward ratio

#### SHORT Signal

Generated when:
- Stop hunt confirmed with rejection
- Bearish delta divergence
- Absorption at resistance
- Score ≥ 6

**Entry**: Current market price  
**Stop Loss**: Above swept high (0.2% buffer)  
**Target**: Based on risk/reward ratio

#### MONITOR Signal

Generated when:
- Patterns detected but not confirmed
- Waiting for additional confirmation
- Score < 6

**Action**: Watch for signal upgrade to MEDIUM/HIGH

### Market Phases

1. **NONE** - No significant patterns detected
2. **ABSORPTION_ACTIVE** - Large orders being absorbed
3. **STOP_HUNT_OCCURRED** - Liquidity sweep detected
4. **DELTA_CONFIRMED** - Delta confirms direction
5. **ENTRY_CONFIRMED** - All conditions met for entry

### Example Signal Output

```json
{
  "signal": "LONG",
  "conviction": "HIGH",
  "total_score": 9,
  "phase": "ENTRY_CONFIRMED",
  "entry": {
    "price": 75600.00,
    "type": "MARKET"
  },
  "stop_loss": {
    "price": 75450.00,
    "type": "FIXED"
  },
  "reasons": [
    "Confirmed stop hunt with reclaim + delta flip",
    "Strong absorption (4 candles)",
    "Bullish delta divergence"
  ]
}
```

---

## Telegram Notifications

### Setup

1. Create a Telegram bot via @BotFather
2. Get your bot token
3. Get your chat ID (message @userinfobot)
4. Edit `.env` file:

```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

5. Restart the system:

```bash
./start-all.sh restart
```

### Notification Triggers

Telegram alerts are sent when:
- Signal is LONG or SHORT
- Conviction is HIGH or MEDIUM
- Score threshold is met

### Message Format

```
🟢 INSTITUTIONAL SIGNAL 🔥

Signal: LONG
Conviction: HIGH
Score: +9

Entry: $75,600.00
Stop Loss: $75,450.00

Reasons:
• Confirmed stop hunt with reclaim + delta flip
• Strong absorption (4 candles)
• Bullish delta divergence

Timestamp: 2024-01-15 14:30:00 UTC
```

### Test Notifications

```bash
curl -X POST http://localhost:8000/telegram/test
```

---

## System Management

### Start/Stop Commands

```bash
# Start both backend and dashboard
./start-all.sh start

# Stop all services
./start-all.sh stop

# Restart everything
./start-all.sh restart

# Check status
./start-all.sh status
```

### Process Management

The system tracks PIDs for both services:
- Backend PID: `server.pid`
- Dashboard PID: `dashboard.pid`

Logs are stored in `logs/` directory:
- `backend.log` - Backend server logs
- `backend-error.log` - Backend errors
- `dashboard.log` - Dashboard logs
- `dashboard-build.log` - Build output

### Viewing Logs

```bash
# Backend logs
tail -f logs/backend.log

# Dashboard logs
tail -f logs/dashboard.log

# Errors only
tail -f logs/backend-error.log
```

### Auto-Start on Boot (macOS)

The system includes a launchd configuration for automatic startup:

```bash
# Install auto-start
cp com.institutional.footprint.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.institutional.footprint.plist

# Remove auto-start
launchctl unload ~/Library/LaunchAgents/com.institutional.footprint.plist
rm ~/Library/LaunchAgents/com.institutional.footprint.plist
```

### Manual Start

```bash
# Start backend only
cd /Users/mac/institutional-footprint
nohup python3 server.py > logs/backend.log 2>&1 &
echo $! > server.pid

# Start dashboard only
cd web-dashboard
PORT=3001 nohup npm start > ../logs/dashboard.log 2>&1 &
echo $! > ../dashboard.pid
```

---

## Troubleshooting

### Dashboard Not Loading

**Problem**: http://localhost:3001 shows error

**Solution**:
```bash
# Check if dashboard is running
cat dashboard.pid
ps -p $(cat dashboard.pid)

# Restart dashboard
./start-all.sh restart
```

### No Data Showing

**Problem**: Dashboard shows price $0.00 or empty charts

**Possible Causes**:
1. WebSocket not connected
2. Symbol has low liquidity
3. Backend not running

**Solution**:
```bash
# Check backend status
curl http://localhost:8000/health

# Check backend logs
tail -20 logs/backend.log | grep ENGINE

# Verify WebSocket connection
tail -20 logs/backend.log | grep "Received message"
```

### Symbol Not Receiving Data

**Problem**: PAXGUSDT shows $0.00

**Cause**: Lower liquidity means fewer trades

**Solution**: Wait for more market activity, or focus on BTC/ETH which have higher volume

### High CPU Usage

**Problem**: System using too much CPU

**Solution**:
```bash
# Check resource usage
top -pid $(cat server.pid)
top -pid $(cat dashboard.pid)

# Reduce polling frequency (edit page.tsx)
const interval = setInterval(fetchData, 5000); // Change from 3000 to 5000
```

### Telegram Not Sending

**Problem**: No Telegram notifications

**Solution**:
```bash
# Test Telegram connection
curl -X POST http://localhost:8000/telegram/test

# Check .env file
cat .env | grep TELEGRAM

# Verify bot token is correct
```

### Port Already in Use

**Problem**: Error "Address already in use"

**Solution**:
```bash
# Find process using port
lsof -i :8000  # Backend
lsof -i :3001  # Dashboard

# Kill the process
kill -9 <PID>

# Restart
./start-all.sh restart
```

### Memory Issues

**Problem**: System running out of memory

**Solution**:
```bash
# Check memory usage
memory_pressure

# Reduce number of monitored symbols
# Edit server.py and remove less important symbols
```

---

## Advanced Configuration

### Adjusting Detection Thresholds

Edit `/Users/mac/institutional-footprint/engine.py`:

```python
# Wall detection thresholds
LARGE_WALL_THRESHOLD = 50.0          # BTC — adjust per asset
WALL_REFRESH_THRESHOLD = 3           # Times wall must refresh
SPOOF_CANCEL_THRESHOLD = 0.8         # 80% cancellation rate

# Absorption detection
ABSORPTION_DURATION_MIN = 2          # Minimum candles
ABSORPTION_SIZE_RATIO = 1.5          # Size vs average

# Stop hunt detection
SWEEP_PERCENTAGE = 0.002             # 0.2% beyond level
CONFIRMATION_CANDLES = 1             # Candles to confirm
```

### Customizing Signal Generation

Modify the `generate_signal()` method in `engine.py` to adjust scoring weights or add new patterns.

### Adding Custom Indicators

1. Create new detection method in `engine.py`
2. Add to `build_market_state()` return dict
3. Update dashboard to display new metric
4. Include in signal scoring if relevant

### API Rate Limiting

The system polls every 3 seconds by default. To change:

Edit `/Users/mac/institutional-footprint/web-dashboard/app/page.tsx`:

```typescript
const interval = setInterval(fetchData, 5000); // 5 seconds
```

### Database Integration (Future)

To add persistent storage:

1. Install database (PostgreSQL recommended)
2. Create signal history table
3. Modify `on_signal` callback to save to DB
4. Add endpoint to retrieve historical signals

### Deployment to VPS

For 24/7 cloud deployment:

1. Set up Ubuntu VPS (DigitalOcean, AWS, etc.)
2. Install Python and Node.js
3. Clone repository
4. Install dependencies
5. Configure systemd service
6. Set up reverse proxy (nginx)
7. Enable SSL (Let's Encrypt)

---

## API Reference

### Endpoints

#### Health Check
```
GET /health
```
Returns system health status.

#### Market State (Single Symbol)
```
GET /state
```
Returns current market state for default symbol.

#### Market State (All Symbols)
```
GET /multi/state
```
Returns market state for all monitored symbols.

#### Signal History
```
GET /signals/history
```
Returns recent signal history.

#### Multi-Symbol Summary
```
GET /multi/summary
```
Returns compact summary for dashboard grid.

#### Supported Symbols
```
GET /symbols
```
Returns list of supported and current symbols.

#### Switch Symbol
```
POST /symbol/switch
Content-Type: application/json

{"symbol": "BTCUSDT"}
```
Switches the default symbol (single-symbol mode).

#### Telegram Test
```
POST /telegram/test
```
Sends test notification to Telegram.

#### Force Signal
```
POST /force-signal
```
Generates signal immediately (for testing).

### Response Formats

#### Market State
```json
{
  "price": 75600.00,
  "delta": 3.62,
  "cumulative_delta": 125.45,
  "absorption": {
    "detected": true,
    "side": "buy",
    "duration_candles": 4
  },
  "iceberg": {
    "detected": false,
    "side": "none",
    "refresh_count": 0
  },
  "stop_hunt": {
    "detected": true,
    "direction": "long_stop_hunt",
    "confirmed": true
  },
  "divergence": "bullish",
  "spoofs_60s": 2,
  "top_bids": [...],
  "top_asks": [...]
}
```

#### Signal
```json
{
  "signal": "LONG",
  "conviction": "HIGH",
  "total_score": 9,
  "phase": "ENTRY_CONFIRMED",
  "entry": {
    "price": 75600.00,
    "type": "MARKET"
  },
  "stop_loss": {
    "price": 75450.00,
    "type": "FIXED"
  },
  "reasons": [
    "Confirmed stop hunt with reclaim + delta flip",
    "Strong absorption (4 candles)"
  ],
  "timestamp": 1705329000
}
```

---

## Security Considerations

### API Keys

⚠️ **Never commit API keys to Git**

The `.env` file is in `.gitignore`. Keep it secure:

```bash
chmod 600 .env
```

### Network Security

- Backend runs on localhost by default
- Dashboard accessible only locally
- For remote access, use SSH tunnel or VPN

### Production Deployment

If deploying publicly:
1. Use HTTPS (SSL certificate)
2. Add authentication
3. Implement rate limiting
4. Use environment variables for secrets
5. Regular security updates

---

## Performance Optimization

### Recommended Settings

- **Polling Interval**: 3-5 seconds (balance between freshness and load)
- **Monitored Symbols**: 3-5 (more symbols = more resources)
- **Log Rotation**: Implement log rotation for long-term operation
- **Memory Limits**: Monitor and restart if memory exceeds 2GB

### Resource Usage

Typical resource consumption:
- **CPU**: 5-15% (varies with market volatility)
- **Memory**: 200-500 MB
- **Network**: 1-5 Mbps (WebSocket streams)
- **Disk**: Minimal (logs only)

---

## Support & Resources

### Documentation Files

- `README.md` - Project overview
- `DASHBOARD_QUICKSTART.md` - Dashboard quick reference
- `INSTITUTIONAL_FOOTPRINT_GUIDE.pdf` - This guide

### Code Structure

```
institutional-footprint/
├── engine.py              # Core detection engine
├── server.py              # FastAPI backend
├── multi_engine.py        # Multi-symbol manager
├── telegram_notifier.py   # Telegram integration
├── volume_profile.py      # Volume profile calculator
├── web-dashboard/         # Next.js dashboard
│   ├── app/
│   │   ├── page.tsx       # Single symbol view
│   │   └── multi/page.tsx # Multi-symbol view
│   └── ...
├── logs/                  # Runtime logs
├── start-all.sh           # Management script
└── .env                   # Configuration (not in git)
```

### Getting Help

1. Check logs for error messages
2. Review this troubleshooting section
3. Verify all services are running
4. Test individual components

---

## Version Information

**Current Version**: 2.0.0  
**Last Updated**: April 2026  
**Features**: Multi-symbol monitoring, Telegram alerts, Web dashboard  

### Changelog

**v2.0.0** (April 2026)
- Added multi-symbol simultaneous monitoring
- Created grid dashboard for all symbols
- Improved WebSocket reliability
- Added PAXGUSDT support

**v1.0.0** (March 2026)
- Initial release
- Single symbol monitoring
- Rule-based signal detection
- Web dashboard
- Telegram notifications

---

## License & Disclaimer

### Trading Disclaimer

This system is for **educational and informational purposes only**. It does not constitute financial advice. Cryptocurrency trading involves substantial risk of loss. Always do your own research and consider your risk tolerance before trading.

### No Guarantees

- Past performance does not guarantee future results
- Signals may be incorrect or delayed
- Market conditions can change rapidly
- Use proper risk management at all times

### Responsibility

You are solely responsible for:
- Trading decisions made using this system
- Risk management and position sizing
- Compliance with local regulations
- Tax obligations on trading profits

---

## Quick Reference Card

### URLs
- Single Dashboard: http://localhost:3001
- Multi Dashboard: http://localhost:3001/multi
- API Health: http://localhost:8000/health

### Commands
```bash
./start-all.sh start      # Start system
./start-all.sh stop       # Stop system
./start-all.sh restart    # Restart system
./start-all.sh status     # Check status
tail -f logs/backend.log  # View logs
```

### Key Shortcuts
- Switch symbols: Use dropdown in header
- Refresh data: Click refresh button
- Multi-view: Click "MULTI-SYMBOL VIEW" button
- Back to single: Navigate to http://localhost:3001

### Signal Colors
- 🟢 Green = LONG/Bullish
- 🔴 Red = SHORT/Bearish
- 🟡 Yellow = MONITOR/Neutral

---

*End of Guide*

For questions or issues, check the logs and review the troubleshooting section.
