# Institutional Entry Detection System

Real-time institutional order flow detection for Binance. Detects whale accumulation, stop hunts, absorption, and iceberg orders — fires signal only when all conditions are met.

**✨ NO API KEYS REQUIRED - 100% Rule-Based Detection ✨**

**Features:**
- 🔄 Real-time market data via Binance WebSocket
- 🎯 Rule-based signal generation (NO LLM costs!)
- 📊 **Live Web Dashboard** - Beautiful real-time UI at http://localhost:3001
- 📱 Telegram notifications for trading signals
- ♾️ 24/7 operation with auto-restart and health monitoring
- 📈 Volume profile integration (POC, VAH, VAL)
- ⚡ Instant signal generation on candle close

---

## Architecture

```
Binance WebSocket (depth + trades)
        ↓
Python Engine (engine.py)
  - Order book tracking
  - Absorption detection
  - Iceberg detection
  - Stop hunt detection
  - Delta divergence
  - Spoof detection
        ↓
FastAPI Server (server.py)
  - REST endpoints
  - WebSocket broadcast
        ↓
React Frontend (App.jsx)
  - Live DOM
  - Phase tracker
  - Fingerprint panel
  - Signal card
  - Signal history
        ↓
Anthropic LLM (claude-sonnet-4)
  - Reads structured payload
  - Returns signal JSON
  - Fires on candle close (5m)
```

---

## Setup

### 1. Backend Setup

```bash
cd institutional-footprint
pip install -r requirements.txt
```

Create your environment file:
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```python
# Optional: Telegram notifications (recommended)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id_from_userinfobot

# Trading configuration
SYMBOL=BTCUSDT
```

**Note:** No API keys required! The system uses rule-based detection instead of LLM.

Start the server:
```bash
# Start both backend and web dashboard (recommended)
./start-all.sh start

# Or use process manager for backend only
./manage.sh start

# Or run directly
python server.py
```

Server runs on `http://localhost:8000`
Web Dashboard runs on `http://localhost:3001`

**Process Management:**
```bash
./start-all.sh status   # Check all services
./start-all.sh restart  # Restart everything
./start-all.sh stop     # Stop all services
./start-all.sh logs     # View backend logs
./start-all.sh dashboard-logs  # View dashboard logs
```

---

### Web Dashboard

The system includes a beautiful real-time web dashboard:

**Features:**
- Live price and market metrics
- Real-time delta chart
- Order book DOM visualization
- Current signal with entry/stop/targets
- Fingerprint detection panel
- Signal history
- Connection status monitoring

**Access:** http://localhost:3001

**24/7 Auto-Start (macOS):**
```bash
# Install launchd service
cp com.institutional.footprint.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.institutional.footprint.plist

# The system will now auto-start on boot and restart on failure
```

---

### 2. Frontend Setup

The frontend is a single-file React app. You can run it with any static file server:

**Option A: Using Vite (Recommended)**
```bash
npm create vite@latest frontend -- --template react
cd frontend
# Replace src/App.jsx with the provided App.jsx
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

**Option B: Quick test with Python**
```bash
# From the institutional-footprint directory
python3 -m http.server 3000
# Then open http://localhost:3000 and serve App.jsx
```

---

### 3. Telegram Setup (Optional)

To receive trading signals via Telegram:

1. **Create a Bot:**
   - Message `@BotFather` on Telegram
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. **Get Your Chat ID:**
   - Message `@userinfobot` on Telegram
   - Copy your chat ID

3. **Add to `.env`:**
   ```
   TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   TELEGRAM_CHAT_ID=123456789
   ```

4. **Test Integration:**
   ```bash
   curl -X POST http://localhost:8000/telegram/test
   ```

---

## Signal Generation (Rule-Based)

The system uses a **scoring algorithm** to detect institutional activity and generate signals:

### Scoring System

| Fingerprint | Max Score | Conditions |
|-------------|-----------|------------|
| Absorption | +3 | 3+ candles = +3, 2 candles = +2, 1 candle = +1 |
| Iceberg Orders | +2 | 8+ refreshes = +2, <8 refreshes = +1 |
| Stop Hunt | +4 | Confirmed (reclaim + delta flip) = +4, Reclaim only = +3, Detected = +2 |
| Delta Divergence | +2 | Bullish or bearish divergence detected |
| Volume Spike | +1 | 3x+ average volume |

### Signal Thresholds

- **MONITOR:** Score < 6 (watching for setup)
- **MEDIUM:** Score 6-8 (potential opportunity)
- **HIGH:** Score 9+ (strong institutional activity)

### Entry Conditions

Signals fire LONG/SHORT only when:
1. Stop hunt is **confirmed** (price reclaimed + delta flipped)
2. Minimum conviction score of 6
3. Clear entry, stop loss, and take profit levels

---

## 24/7 Deployment

### Option 1: Linux Server with Systemd (Recommended)

1. **Copy service file:**
   ```bash
   sudo cp institutional-footprint.service /etc/systemd/system/
   ```

2. **Edit the service file** and replace:
   - `YOUR_USERNAME` with your username
   - `/path/to/institutional-footprint` with actual path

3. **Enable and start:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable institutional-footprint
   sudo systemctl start institutional-footprint
   ```

4. **Check status:**
   ```bash
   sudo systemctl status institutional-footprint
   journalctl -u institutional-footprint -f  # View logs
   ```

### Option 2: macOS with Launchd

Use the provided `manage.sh` script or create a launchd plist.

### Option 3: Docker (Coming Soon)

---

## Vercel Deployment

**Note:** Vercel is designed for serverless functions and static sites. For this real-time WebSocket application, you have two options:

### Option A: Deploy Frontend Only on Vercel

1. Create a `frontend/` directory with your React app
2. Update `App.jsx` API URLs to point to your backend server
3. Deploy to Vercel:
   ```bash
   cd frontend
   vercel --prod
   ```

### Option B: Full Stack on Vercel (Serverless)

For Vercel deployment, you'll need to refactor the backend to use serverless functions. This requires:
- Converting WebSocket connections to HTTP polling
- Using external services for state management (Redis, Supabase)
- Implementing scheduled jobs for continuous monitoring

**Recommended architecture for Vercel:**
```
Vercel Functions (API routes)
    ↓
External Database (Supabase/Redis)
    ↓
Separate VPS/Cloud Run for WebSocket engine
```

### Option C: Hybrid Approach (Best)

- **Backend:** Deploy on a VPS (DigitalOcean, AWS EC2, Railway) for 24/7 WebSocket connection
- **Frontend:** Deploy on Vercel for CDN and edge caching
- **Database:** Use Supabase for signal history persistence

**Deploy Backend to Railway/Render:**
1. Push code to GitHub
2. Connect repository to Railway/Render
3. Set environment variables
4. Deploy automatically

**Deploy Frontend to Vercel:**
```bash
vercel --prod
```

---

## Configuration (engine.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| SYMBOL | BTCUSDT | Trading pair |
| LARGE_WALL_THRESHOLD | 50.0 | Min BTC for wall detection |
| SPOOF_MAX_AGE_MS | 5000 | Wall age threshold for spoof |
| SPOOF_MIN_SIZE_RATIO | 15 | Size vs nearby depth for spoof |
| ICEBERG_MIN_REFRESHES | 5 | Min refreshes for iceberg |
| ABSORPTION_MAX_PRICE_MOVE_PCT | 0.05 | Max price move during absorption |
| VOLUME_SPIKE_RATIO | 3.0 | Volume spike multiplier |
| CANDLE_TIMEFRAME_SECONDS | 300 | 5 min candles |

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /state | GET | Current market state |
| /signal | GET | Latest signal |
| /signals/history | GET | Last 100 signals |
| /payload | GET | Current LLM input payload |
| /health | GET | Health check for monitoring |
| /signal/force | POST | Force immediate LLM analysis |
| /telegram/test | POST | Test Telegram notifications |
| /ws | WS | Real-time market + signal updates |

---

## Signal Phases

```
PHASE 1 — ACCUMULATION     → MONITOR signal
PHASE 2 — STOP HUNT        → MONITOR signal (prepare)  
PHASE 3 — ENTRY CONFIRMED  → LONG / SHORT signal
PHASE 4 — MARKUP           → Manage trade
```

Signal fires LONG/SHORT only at Phase 3.
Phase 3 requires: stop hunt + reclaim + delta flip.

---

## Volume Profile Integration

✅ **Fully Implemented**

The system now includes real-time volume profile calculation:
- **POC (Point of Control):** Price level with highest traded volume
- **VAH (Value Area High):** Upper boundary of 70% value area
- **VAL (Value Area Low):** Lower boundary of 70% value area
- **Session Management:** Automatically resets every 50 candles

Volume profile data is included in the LLM payload for enhanced signal analysis.

---

## Notes

- LLM is called every 5m candle close by default
- Use POST /signal/force to trigger on-demand analysis
- Adjust LARGE_WALL_THRESHOLD based on your asset's typical liquidity
- For non-BTC pairs, reduce wall thresholds significantly
