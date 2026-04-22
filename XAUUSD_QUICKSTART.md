# XAUUSD SMC Monitor - Quick Start Guide

## 📍 All Files Are Located In:
**`/Users/mac/institutional-footprint/`**

---

## ✅ Files Created:

1. **xauusd_smc_monitor.py** - Main monitoring engine (575 lines)
2. **XAUUSDSMCDashboard.jsx** - React dashboard component (256 lines)
3. **start_xauusd_smc.sh** - Startup script (executable)
4. **XAUUSD_SMC_README.md** - Full documentation
5. **XAUUSD_QUICKSTART.md** - This file

## ✅ Files Modified:

6. **server.py** - Added `/api/xauusd-smc` endpoints
7. **requirements.txt** - Added `python-dotenv`
8. **.env** - Added `TWELVE_DATA_API_KEY` placeholder

---

## 🚀 Get Started in 3 Steps:

### Step 1: Add Your Twelve Data API Key

Get your FREE API key from: https://twelvedata.com

Then edit `.env`:
```bash
nano /Users/mac/institutional-footprint/.env
```

Replace this line:
```
TWELVE_DATA_API_KEY=your_twelve_data_api_key_here
```

With your actual key:
```
TWELVE_DATA_API_KEY=abc123xyz456...
```

Save with `Ctrl+O`, exit with `Ctrl+X`

### Step 2: Install Dependencies

```bash
cd /Users/mac/institutional-footprint
pip install python-dotenv
```

### Step 3: Run the Monitor

**Option A - Using startup script:**
```bash
./start_xauusd_smc.sh
```

**Option B - Direct execution:**
```bash
python3 xauusd_smc_monitor.py
```

---

## 📊 Access the Dashboard

### API Endpoints (Available Now):

Once the monitor is running, access these URLs:

- **Full SMC Data:** http://localhost:8000/api/xauusd-smc
- **Signals Only:** http://localhost:8000/api/xauusd-smc/signals

### Web Dashboard (Optional):

To add the visual dashboard to your Next.js app:

1. Copy the dashboard component:
```bash
cp XAUUSDSMCDashboard.jsx web-dashboard/app/xauusd-smc/page.jsx
```

2. Add a navigation link in your app

Or create a simple HTML page that fetches from the API endpoints above.

---

## 🔍 What You'll See

### Console Output:
```
============================================================
XAUUSD Smart Money Concepts Monitor Started
============================================================
Symbol: XAUUSD
Timeframe: 5min
HTF Timeframe: 4h
Monitoring Interval: 300s
============================================================

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
```

### API Response Example:
```json
{
  "status": "success",
  "data": {
    "timestamp": "2025-04-22T14:30:00",
    "current_price": 2345.67,
    "atr": 12.45,
    "htf_bias": "bullish",
    "structures": [
      {"type": "BOS", "direction": "bullish"}
    ],
    "active_fvgs": 3,
    "liquidity_zones": 8,
    "signals": [
      {
        "type": "BOS",
        "direction": "bullish",
        "price": 2345.67,
        "confidence": 0.85,
        "description": "BOS BULLISH | HTF: bullish | FVG: Yes | Liq: Yes"
      }
    ]
  }
}
```

---

## 📝 Strategy Overview

The monitor detects **Smart Money Concepts** patterns:

✅ **BOS (Break of Structure)** - Trend continuation  
✅ **CHOCH (Change of Character)** - Trend reversal  
✅ **FVG (Fair Value Gaps)** - Price imbalances  
✅ **Liquidity Zones** - Buy/sell side targets  
✅ **HTF Bias** - 4-hour trend direction  

**Signal Confidence Scoring:**
- Base: 50%
- HTF alignment: +20%
- FVG present: +15%
- Liquidity nearby: +15%
- **Minimum threshold: 60%**

---

## 🛠️ Monitoring & Logs

### View Real-Time Logs:
```bash
tail -f logs/xauusd_smc.log
```

### Check Current State:
```bash
cat xauusd_smc_state.json
```

### Test API Endpoint:
```bash
curl http://localhost:8000/api/xauusd-smc
```

---

## ⚙️ Configuration

### Change Monitoring Interval:
Edit `xauusd_smc_monitor.py`, line ~440:
```python
self.monitoring_interval = 300  # Change from 300 (5 min) to desired seconds
```

### Adjust Sensitivity:
Edit `xauusd_smc_monitor.py`, line ~435:
```python
self.analyzer = SmartMoneyAnalyzer(swing_length=10, detection_length=7)
# Lower values = more sensitive, Higher values = less sensitive
```

---

## ❓ Troubleshooting

### "No data available yet"
- The monitor needs to run at least one cycle (5 minutes)
- Wait for the first analysis to complete
- Check logs: `tail -f logs/xauusd_smc.log`

### "API Error" or connection issues
- Verify your Twelve Data API key is correct
- Check internet connection
- Free tier limit: 800 requests/day (monitor uses ~576/day)

### No signals generated
- This is normal! Signals require ≥60% confidence
- Multiple factors must align (structure + bias + FVG/liquidity)
- May take hours or days for high-quality setups

### Module not found errors
```bash
pip install -r requirements.txt
```

---

## 🎯 Next Steps

1. ✅ **Monitor running** - Generate real-time signals
2. ⏳ **Add Telegram alerts** - Use existing `telegram_notifier.py`
3. ⏳ **Deploy dashboard** - Integrate into Next.js app
4. ⏳ **Auto-start on boot** - Create systemd/plist service
5. ⏳ **Backtesting** - Test strategy on historical data

---

## 📞 Support

Check the full documentation:
```bash
cat XAUUSD_SMC_README.md
```

View logs for debugging:
```bash
tail -100 logs/xauusd_smc.log
```

---

**Ready to trade smarter with institutional concepts! 🚀**
