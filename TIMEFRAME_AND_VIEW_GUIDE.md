# 📊 Timeframe & View Configuration

## Current Configuration

### ⏱️ **5-Minute Candle Timeframe**

All institutional footprint detection is based on **5-minute candles**:

```python
# From engine.py line 42
CANDLE_TIMEFRAME_SECONDS = 300  # 5 min candles
```

### What This Means:

1. **Candle Formation**: 
   - Each candle represents 5 minutes of trading data
   - Candles align to 5-minute intervals (e.g., 10:00, 10:05, 10:10 UTC)
   
2. **Signal Generation**:
   - Signals are evaluated every 5 minutes at candle close
   - Latest signal updated every 300 seconds
   
3. **Detection Algorithms**:
   - Absorption detection: Analyzes price action within 5m candles
   - Iceberg orders: Tracked across 5m candle boundaries
   - Stop hunts: Measured relative to 5m candle highs/lows
   - Delta divergence: Calculated over 5m candle periods

---

## 🔄 View Toggle Feature

### Single View vs Multi-Symbol View

You can now easily switch between two dashboard views:

#### **Single Symbol View** (`/`)
- **Focus**: Deep analysis of one symbol at a time
- **Features**:
  - Detailed order book visualization
  - Delta history chart
  - Full fingerprint detection details
  - Market phase progress indicator
  - Signal history timeline
  - Entry/Stop/Target levels
  
- **Use When**:
  - Trading one specific pair (e.g., BTCUSDT)
  - Need detailed order flow analysis
  - Want to see full signal rationale

#### **Multi-Symbol View** (`/multi`)
- **Focus**: Overview of multiple markets simultaneously
- **Features**:
  - Grid layout showing all symbols
  - Current price for each symbol
  - Signal status at a glance
  - Conviction level badges
  - Fingerprint indicators
  - Spoof counters
  
- **Use When**:
  - Monitoring multiple pairs (BTC, ETH, PAXG)
  - Looking for best setup across markets
  - Need quick status overview

### How to Switch Views:

**Header Toggle Button** (visible on both pages):

```
┌─────────────────────────────────────┐
│ [SINGLE]  [MULTI]                  │
└─────────────────────────────────────┘
   Active    Inactive
```

- **Single View**: Click "SINGLE" button (or go to `/`)
- **Multi View**: Click "MULTI" button (or go to `/multi`)

**Visual Indicators**:
- Active view has **blue background**
- Inactive view has **gray background**
- Icons show List (single) vs Grid (multi)

---

## 📈 Timeframe Details

### Candle Construction

```
5-Minute Candle Structure:
┌─────────────────────────────────┐
│ Time:     14:00:00 - 14:04:59   │
│ Open:     $78,241.94            │
│ High:     $78,285.50            │
│ Low:      $78,230.10            │
│ Close:    $78,260.25            │
│ Volume:   152.5 BTC             │
│ Delta:    +3.21 BTC             │
└─────────────────────────────────┘
```

### Detection Windows

| Metric | Time Window | Description |
|--------|-------------|-------------|
| Spoofs | 60 seconds | Rolling window for spoof detection |
| Candles | 5 minutes | Primary analysis timeframe |
| Signal Generation | 5 minutes | Evaluated at candle close |
| Volume Spike | 5 minutes | Current vs average volume |
| Delta Divergence | 3 candles (15 min) | Multi-candle pattern |
| Absorption | 5 minutes | Price action within candle |
| Iceberg | Multi-candle | Tracked across candles |

### Why 5-Minute Timeframe?

**Advantages**:
1. ✅ Fast enough for intraday trading
2. ✅ Reduces noise compared to 1m candles
3. ✅ Captures institutional order flow patterns
4. ✅ Good balance between speed and reliability
5. ✅ Aligns with common trading strategies

**Compared to Other Timeframes**:
- **1-minute**: Too noisy, many false signals
- **5-minute**: ✅ Optimal for institutional detection
- **15-minute**: Slower signals, miss short setups
- **1-hour**: Too slow for real-time trading

---

## 🎯 Current Monitored Symbols

All running on **5-minute timeframe**:

| Symbol | Market | Price Range | Volatility |
|--------|--------|-------------|------------|
| BTCUSDT | Bitcoin | ~$78k | High |
| ETHUSDT | Ethereum | ~$2.4k | Medium-High |
| PAXGUSDT | Gold Token | ~$4.7k | Low-Medium |
| XAUUSDT | Gold | Ready | Low |

---

## 🔧 Configuration

### Change Timeframe (Advanced)

To modify the candle timeframe:

**File**: `engine.py`

```python
# Line 42
CANDLE_TIMEFRAME_SECONDS = 300  # Change this value

# Options:
# 60   = 1 minute candles
# 300  = 5 minute candles (CURRENT)
# 900  = 15 minute candles
# 3600 = 1 hour candles
```

**Important**: After changing, restart the backend:
```bash
ssh root@165.22.55.118
cd /root/institutional-footprint
./start-all.sh restart
```

### Dashboard UI Shows Timeframe

Both views now display the active timeframe:

**Single View**:
```
INSTITUTIONAL FOOTPRINT
Real-time Order Flow Detection System | 5m Timeframe
```

**Multi View**:
```
INSTITUTIONAL FOOTPRINT
Multi-Symbol Real-Time Monitoring | 5m Timeframe
```

---

## 📊 Data Flow

```
Binance WebSocket (Real-time)
    ↓
Trade Stream (tick-by-tick)
    ↓
Aggregated into 5-Minute Candles
    ↓
InstitutionalEntryEngine Analysis
    ↓
Signal Generation (every 5m)
    ↓
Dashboard Display (updates every 3s)
```

### Update Frequencies:

| Component | Update Rate | Purpose |
|-----------|-------------|---------|
| WebSocket | Real-time (100ms) | Live price/orders |
| Order Book | 100ms | Depth visualization |
| Candles | Every 5 min | Analysis window |
| Signals | Every 5 min | Trading decisions |
| Dashboard Poll | Every 3 sec | UI refresh |
| Telegram Alerts | On signal | Notifications |

---

## 🎨 UI Features

### View Toggle Location

```
┌─────────────────────────────────────────────────────────────┐
│ INSTITUTIONAL FOOTPRINT                   [SINGLE][MULTI]  │
│ Real-time Order Flow Detection System | 5m Timeframe       │
│                                                             │
│ [SYMBOL: BTCUSDT ▼]  [📡 CONNECTED]  [⟳ Refresh]          │
└─────────────────────────────────────────────────────────────┘
```

### Toggle States:

**On Single View**:
- SINGLE button: 🔵 Blue background (active)
- MULTI button: ⚫ Gray background (inactive)

**On Multi View**:
- SINGLE button: ⚫ Gray background (inactive)
- MULTI button: 🔵 Blue background (active)

---

## 📱 Access URLs

### With New View Toggle:

- **Dashboard**: http://165.22.55.118:3001
  - Click toggle to switch views
  
- **Single View**: http://165.22.55.118:3001/
  - Direct link to single symbol view
  
- **Multi View**: http://165.22.55.118:3001/multi
  - Direct link to multi-symbol view

---

## 🧪 Testing the Toggle

1. **Open Dashboard**: http://165.22.55.118:3001
2. **Check Timeframe**: See "| 5m Timeframe" in header
3. **Test Toggle**:
   - Click "MULTI" → Should navigate to grid view
   - Click "SINGLE" → Should return to detailed view
4. **Verify Active State**: Active button shows blue background
5. **Check Both Views**: Both display "5m Timeframe" indicator

---

## 📝 Summary

**Timeframe**: 5-minute candles  
**Single View**: Deep analysis (1 symbol)  
**Multi View**: Overview (all symbols)  
**Toggle**: Header button (easy switching)  
**Display**: Shows "| 5m Timeframe" in both views  

All detection algorithms, signals, and analysis are optimized for 5-minute candle patterns! 🚀
