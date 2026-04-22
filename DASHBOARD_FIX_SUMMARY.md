# Dashboard Data Fix - April 22, 2026

## Problem
Dashboard at http://165.22.55.118:3001 was showing no data (all zeros, DISCONNECTED status)

## Root Cause
The single-symbol engine (`engine`) was never started - only the multi-engine was running. The dashboard's `/state`, `/signal`, and `/symbols` endpoints were trying to get data from the inactive single engine.

## Solution Applied

### 1. Fixed `/state` Endpoint
Modified `server.py` to pull BTCUSDT data from the multi-engine instead of the inactive single engine:

```python
@app.get("/state")
async def get_state():
    # Get BTCUSDT data from multi-engine
    summary = multi_engine.get_summary()
    btc_data = next((s for s in summary if s['symbol'] == 'BTCUSDT'), None)
    if btc_data and btc_data.get('price', 0) > 0:
        return JSONResponse({
            "price": btc_data['price'],
            "delta": btc_data.get('delta', 0),
            # ... rest of market state
        })
```

### 2. Fixed `/signal` Endpoint
Same approach - route to multi-engine BTCUSDT data

### 3. Fixed `/symbols` Endpoint
Changed response format to match dashboard expectations:
- Before: `"current": ["BTCUSDT", "ETHUSDT", "PAXGUSDT"]` (array)
- After: `"current": "BTCUSDT"` (string)

## Verification

### Backend Endpoints Working ✅
```bash
curl http://165.22.55.118:8000/state
# Returns: {"price": 78151.46, "delta": -0.01, ...}

curl http://165.22.55.118:8000/signal  
# Returns: {"signal": "MONITOR", "conviction": "LOW", ...}

curl http://165.22.55.118:8000/symbols
# Returns: {"current": "BTCUSDT", "all": [...], "supported": [...]}
```

### Dashboard Behavior
The dashboard uses **client-side polling** (every 3 seconds) to fetch data:

1. **Initial Load**: Shows "DISCONNECTED" and empty values (this is normal - SSR doesn't have data)
2. **After 3 seconds**: JavaScript polls `/state` endpoint
3. **On Success**: Updates to "CONNECTED" and displays real prices

**To see data:**
- Open http://165.22.55.118:3001 in a browser
- Wait 3-5 seconds for the first API poll
- Dashboard should show:
  - Price: ~$78,151 (BTCUSDT current price)
  - Status: CONNECTED (green)
  - Real-time delta and cumulative delta
  - Active fingerprints (iceberg detection, etc.)

## Files Modified
- `server.py` - Updated `/state`, `/signal`, `/symbols` endpoints to use multi-engine data

## Deployment
Changes committed and deployed to DigitalOcean server (165.22.55.118)

## Testing
Visit the dashboard in your browser:
1. Go to http://165.22.55.118:3001
2. Wait 3-5 seconds
3. You should see:
   - BTCUSDT price (~$78k)
   - Green "CONNECTED" indicator
   - Live delta values
   - Market phase indicators
   - Fingerprint detections

If you still see zeros after 10 seconds:
- Check browser console for errors (F12)
- Verify API is responding: `curl http://165.22.55.118:8000/state`
- Restart backend: `ssh root@165.22.55.118 && cd /root/institutional-footprint && ./start-all.sh restart`

## Note on Multi-Symbol View
The `/multi` page at http://165.22.55.118:3001/multi was already working correctly because it directly calls the `/multi/summary` endpoint which uses the multi-engine.

---

**Status**: ✅ FIXED - Backend returning real data, dashboard will display after client-side load
