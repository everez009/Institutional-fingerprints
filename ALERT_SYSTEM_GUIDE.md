# 🔔 Signal Alert System

## Overview

The dashboard now includes **visual and voice alerts** when trading signals are detected!

---

## ✅ Features Deployed

### 1. Visual Alert Banner

**Single Symbol View** (`/`):
- Large banner appears at top-center of screen
- Color-coded by signal type:
  - 🟢 **Green** = LONG signal
  - 🔴 **Red** = SHORT signal  
  - 🟡 **Yellow** = MONITOR signal
- Shows: Signal type, conviction level, score, symbol, time
- Auto-dismisses after 8 seconds
- Manual close button (✕)

**Multi-Symbol View** (`/multi`):
- Stack of alert cards in top-right corner
- Shows last 5 signals across all symbols
- Each card shows: Symbol, signal, conviction, score, time
- Color-coded by signal type
- Click ✕ to dismiss individual alerts

### 2. Voice Alerts

**Single View**:
- Speaks when ANY new signal detected
- Says: "LONG signal detected. HIGH conviction. Score: 9."
- Uses browser's built-in speech synthesis
- Toggle button: 🔊 (on) / 🔇 (off)

**Multi View**:
- Speaks for HIGH or MEDIUM conviction signals only
- Says: "BTCUSDT LONG signal. HIGH conviction."
- Reduces noise by ignoring LOW conviction
- Toggle button: 🔊 (on) / 🔇 (off)

---

## 🎨 Visual Examples

### Single View Alert (LONG Signal):
```
┌─────────────────────────────────────────────────────────────┐
│  🟢  LONG Signal | HIGH Conviction | Score: +9              │
│      BTCUSDT | 2:45:30 PM                         [✕]      │
└─────────────────────────────────────────────────────────────┘
     ▲
     Green pulsing banner at top of screen
```

### Single View Alert (SHORT Signal):
```
┌─────────────────────────────────────────────────────────────┐
│  🔴  SHORT Signal | MEDIUM Conviction | Score: +7           │
│      ETHUSDT | 2:45:30 PM                         [✕]      │
└─────────────────────────────────────────────────────────────┘
     ▲
     Red pulsing banner at top of screen
```

### Multi View Alerts (Stacked):
```
┌─────────────────────────────────────┐
│ BTCUSDT: LONG | HIGH | Score: +9    │ [✕]
│ 2:45:30 PM                          │
├─────────────────────────────────────┤
│ ETHUSDT: MONITOR | LOW | Score: +2  │ [✕]
│ 2:43:15 PM                          │
├─────────────────────────────────────┤
│ PAXGUSDT: SHORT | MEDIUM | Score: +7│ [✕]
│ 2:40:22 PM                          │
└─────────────────────────────────────┘
     ▲
     Stacked in top-right corner
```

---

## 🔊 Voice Alert Toggle

**Location**: Header bar (next to refresh button)

**Controls**:
- 🔊 **Blue background** = Voice alerts ON
- 🔇 **Gray background** = Voice alerts OFF

**Click to toggle** voice alerts on/off

---

## 📊 How It Works

### Detection Logic:

1. **Every 3 seconds**: Dashboard polls `/state` or `/multi/summary` API
2. **Compare signals**: Checks if current signal differs from previous
3. **Filter FLAT**: Ignores "FLAT" signals (no action needed)
4. **Trigger alerts**: When new signal detected:
   - Shows visual banner
   - Plays voice alert (if enabled)
   - Updates previous signal tracker

### Alert Conditions:

**Single View**:
- ✅ Any signal change (except FLAT)
- ✅ All conviction levels trigger alerts
- ✅ Voice speaks for all signals

**Multi View**:
- ✅ Signal changes per symbol tracked independently
- ✅ Visual alerts for all signals
- ⚠️ Voice only for HIGH/MEDIUM conviction (reduces noise)

---

## 🎯 Example Scenarios

### Scenario 1: New LONG Signal (BTC)
```
Before: BTCUSDT = MONITOR
After:  BTCUSDT = LONG

→ Visual: 🟢 Green banner appears
→ Voice: "LONG signal detected. HIGH conviction. Score: 9."
→ Action: Banner auto-dismisses in 8 seconds
```

### Scenario 2: Signal Changes (ETH)
```
Before: ETHUSDT = FLAT
After:  ETHUSDT = SHORT

→ Visual: 🔴 Red banner appears
→ Voice: "SHORT signal detected. MEDIUM conviction. Score: 7."
→ Action: Banner stays visible for 8 seconds
```

### Scenario 3: Multiple Symbols (Multi View)
```
BTCUSDT: MONITOR → LONG  (HIGH conviction)
ETHUSDT: FLAT → MONITOR  (LOW conviction)
PAXGUSDT: MONITOR → SHORT (MEDIUM conviction)

→ Visual: 3 alert cards stacked (right side)
→ Voice: "BTCUSDT LONG signal. HIGH conviction."
         "PAXGUSDT SHORT signal. MEDIUM conviction."
         (ETHUSDT skipped - LOW conviction)
```

---

## ⚙️ Configuration

### Voice Alert Settings:

**File**: `web-dashboard/app/page.tsx` (Single View)  
**File**: `web-dashboard/app/multi/page.tsx` (Multi View)

**Current Settings**:
```typescript
// Speech synthesis parameters
utterance.rate = 1.1;    // Slightly faster than normal
utterance.pitch = 1;     // Normal pitch
utterance.volume = 1;    // Full volume
```

**To Adjust**:
- `rate`: 0.5 (slow) to 2.0 (fast)
- `pitch`: 0 (low) to 2.0 (high)
- `volume`: 0 (mute) to 1.0 (max)

### Alert Duration:

**Single View**: 8 seconds auto-dismiss
```typescript
setTimeout(() => setAlertVisible(false), 8000);
```

**Multi View**: Manual dismiss only (stacked alerts)
- Keeps last 5 alerts visible
- Click ✕ to remove individual alerts

---

## 🧪 Testing the Alerts

### Method 1: Wait for Real Signal
1. Open dashboard: http://165.22.55.118:3001
2. Enable voice: Click 🔊 button (should be blue)
3. Wait for market conditions to trigger signal
4. Alert appears when signal changes

### Method 2: Check Signal History
1. Open dashboard
2. Look at "SIGNAL HISTORY" panel (right side)
3. When new signal appears, alert triggers

### Method 3: Test Voice Separately
```javascript
// Open browser console (F12) and run:
const utterance = new SpeechSynthesisUtterance("Test alert. This is a test.");
utterance.rate = 1.1;
window.speechSynthesis.speak(utterance);
```

---

## 📱 Browser Compatibility

**Voice Alerts Work In**:
- ✅ Chrome/Edge (best support)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

**Requirements**:
- Browser must support Web Speech API
- User must grant audio permission (first time)
- Tab must be active (background tabs may not speak)

**If Voice Not Working**:
1. Check browser settings (allow audio)
2. Try different browser
3. Visual alerts still work even if voice disabled
4. Toggle 🔊/ button to test

---

## 🎨 Alert Styling

### Colors:
- **LONG**: Green (`#10B981`)
  - Background: `bg-green-500/20`
  - Border: `border-green-500`
  - Text: `text-green-400`

- **SHORT**: Red (`#EF4444`)
  - Background: `bg-red-500/20`
  - Border: `border-red-500`
  - Text: `text-red-400`

- **MONITOR**: Yellow (`#EAB308`)
  - Background: `bg-yellow-500/20`
  - Border: `border-yellow-500`
  - Text: `text-yellow-400`

### Animation:
- `animate-pulse`: Pulsing glow effect
- Single view: 2s pulse duration
- Multi view: 2s pulse duration

---

## 📊 Alert Data Flow

```
Binance WebSocket
    ↓
InstitutionalEntryEngine
    ↓
Signal Detection (every 5m candle)
    ↓
API: /state or /multi/summary
    ↓
Dashboard Polls (every 3s)
    ↓
Compare: Current vs Previous Signal
    ↓
If Changed & Not FLAT:
    → Show Visual Banner
    → Play Voice Alert (if enabled)
    → Update Previous Signal
    ↓
User Sees Alert & Hears Notification
```

---

## 🚀 Access Your Alerts

**Dashboard**: http://165.22.55.118:3001

**Features**:
- ✅ Visual banner on new signals
- ✅ Voice alerts (toggle on/off)
- ✅ Color-coded by signal type
- ✅ Auto-dismiss or manual close
- ✅ Works on single and multi views

**Multi-Symbol**: http://165.22.55.118:3001/multi
- ✅ Stacked alert cards
- ✅ Per-symbol tracking
- ✅ Voice for HIGH/MEDIUM only

---

## 📝 Summary

**Visual Alerts**: ✅ Pulsing banners with signal details  
**Voice Alerts**: ✅ Speaks signal type and conviction  
**Toggle**: ✅ 🔊/ button in header  
**Colors**: ✅ Green (LONG), Red (SHORT), Yellow (MONITOR)  
**Duration**: ✅ 8s auto-dismiss (single) / stacked (multi)  
**Filtering**: ✅ Ignores FLAT signals  

**Now you'll never miss a signal!** 🎯🔔
