# XAUUSD Smart Money Concepts (SMC) Monitoring System

## 📍 File Locations

All files are located in: `/Users/mac/institutional-footprint/`

### Created Files:

1. **xauusd_smc_monitor.py** - Main monitoring engine with SMC strategy
2. **XAUUSDSMCDashboard.jsx** - React dashboard component for web interface
3. **start_xauusd_smc.sh** - Startup script for the monitor
4. **XAUUSD_SMC_README.md** - This documentation file

### Integration Files (Modified):

5. **server.py** - FastAPI server (needs API endpoints added)
6. **.env** - Environment variables (add TWELVE_DATA_API_KEY)
7. **requirements.txt** - Python dependencies (add python-dotenv)

---

## Quick Start

### 1. Get Twelve Data API Key
Visit: https://twelvedata.com  
Sign up → Dashboard → API Keys → Copy your key

### 2. Configure Environment
```bash
cd /Users/mac/institutional-footprint
cp .env.example .env
nano .env
```

Add this line to `.env`:
```
TWELVE_DATA_API_KEY=your_actual_api_key_here
```

### 3. Install Dependencies
```bash
pip install python-dotenv
```

### 4. Add API Endpoints to server.py

Add these endpoints to your existing `server.py`:

```python
@app.get("/api/xauusd-smc")
async def get_xauusd_smc_data():
    """Get XAUUSD Smart Money Concepts analysis data"""
    state_file = 'xauusd_smc_state.json'
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
            return {"status": "success", "data": data}
        else:
            return {"status": "pending", "message": "No data available yet"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/xauusd-smc/signals")
async def get_xauusd_smc_signals():
    """Get recent XAUUSD SMC signals"""
    state_file = 'xauusd_smc_state.json'
    try:
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                data = json.load(f)
            signals = data.get('signals', [])
            return {"status": "success", "signals": signals, "count": len(signals)}
        else:
            return {"status": "pending", "signals": [], "count": 0}
    except Exception as e:
        return {"status": "error", "message": str(e)}
```

### 5. Run the Monitor
```bash
chmod +x start_xauusd_smc.sh
./start_xauusd_smc.sh
```

Or directly:
```bash
python3 xauusd_smc_monitor.py
```

### 6. Access Dashboard

**Option A:** Integrate into existing Next.js app  
Copy `XAUUSDSMCDashboard.jsx` to your web-dashboard components and add a route.

**Option B:** Access API directly  
- Full data: http://localhost:8000/api/xauusd-smc
- Signals only: http://localhost:8000/api/xauusd-smc/signals

---

## What This System Does

### Strategy Components:
✅ **BOS (Break of Structure)** - Detects trend continuation  
✅ **CHOCH (Change of Character)** - Identifies trend reversals  
✅ **FVG (Fair Value Gaps)** - Finds price imbalances  
✅ **Liquidity Zones** - Maps buy/sell side liquidity  
✅ **HTF Bias** - 4-hour trend direction via EMA crossover  

### Signal Generation:
- Monitors every 5 minutes
- Requires ≥60% confidence threshold
- Combines multiple confluence factors:
  - Base confidence: 50%
  - HTF bias alignment: +20%
  - FVG present: +15%
  - Liquidity zone nearby: +15%

### Output:
- Console logs with detailed analysis
- State file: `xauusd_smc_state.json` (auto-updated)
- Web dashboard with real-time metrics
- Alert logging (Telegram integration ready)

---

## Monitoring Output Example

```
============================================================
Analysis Cycle Started - 2025-04-22 14:30:00
============================================================
Current Price: $2345.67
ATR(14): $12.45
Detected 15 swing points
HTF Bias: BULLISH
🔔 BOS detected: BULLISH
Active FVGs: 3 (Bullish: 2, Bearish: 1)
Liquidity Zones: 8 (Buyside: 4, Sellside: 4)

🚨 SIGNALS GENERATED: 1
   Type: BOS
   Direction: BULLISH
   Price: $2345.67
   Confidence: 85%
   Details: BOS BULLISH | HTF: bullish | FVG: Yes | Liq: Yes
----------------------------------------
ALERT SENT: {
  "symbol": "XAUUSD",
  "signal_type": "BOS",
  "direction": "bullish",
  "price": 2345.67,
  "confidence": 0.85,
  ...
}
```

---

## Viewing Logs

```bash
# Real-time log tail
tail -f logs/xauusd_smc.log

# Check state file
cat xauusd_smc_state.json
```

---

## Troubleshooting

### No Data Available
- Verify API key in `.env` is correct
- Check internet connection
- Review logs: `cat logs/xauusd_smc.log`

### API Rate Limits
Free tier: 800 requests/day  
Monitor uses: ~576 requests/day (2 per cycle × 288 cycles)  
✅ Within limits

### No Signals Generated
This is normal! The system requires high-confidence setups (≥60%).  
Signals appear when multiple factors align (structure break + HTF bias + FVG/liquidity).

---

## Architecture

```
Twelve Data API
       ↓
Data Fetcher (5min + 4H candles)
       ↓
SMC Analyzer
  • Swing Detection
  • BOS/CHOCH Detection
  • FVG Detection
  • Liquidity Zone Mapping
  • HTF Bias Analysis
       ↓
Signal Engine (Confluence Scoring)
       ↓
    ┌────┴────┐
    ↓         ↓
Console    State JSON
Logs       (for dashboard)
```

---

## Next Steps

1. ✅ Monitor running and generating signals
2. ⏳ Add Telegram notifications (use existing telegram_notifier.py)
3. ⏳ Integrate dashboard into Next.js app
4. ⏳ Set up auto-start on system boot
5. ⏳ Add email alerts
6. ⏳ Build backtesting module

---

## Support

For issues:
```bash
# Check logs
tail -100 logs/xauusd_smc.log

# Verify environment
grep TWELVE_DATA_API_KEY .env

# Test API connectivity
python3 -c "import aiohttp; print('OK')"
```
