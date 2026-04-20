# Telegram Quick Reference

## Setup (One-Time)

### Option 1: Interactive Setup Script
```bash
./setup-telegram.sh
```
Follow the prompts - it will guide you through everything!

### Option 2: Manual Setup

1. **Create Bot**: Message @BotFather → `/newbot` → Get token
2. **Get Chat ID**: Message @userinfobot → Copy your ID
3. **Edit .env file**:
   ```bash
   nano .env
   ```
   Update these lines:
   ```env
   TELEGRAM_BOT_TOKEN=your_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```
4. **Restart system**:
   ```bash
   ./start-all.sh restart
   ```

---

## Test Your Setup

### Check Configuration Status
```bash
curl http://localhost:8000/telegram/status
```

Expected response:
```json
{
  "configured": true,
  "bot_token_set": true,
  "chat_id_set": true
}
```

### Send Test Message
```bash
curl -X POST http://localhost:8000/telegram/test
```

You should receive a test notification on Telegram! ✅

---

## Available Notifications

### 1. Trading Signals (Automatic)
Sent automatically when HIGH/MEDIUM conviction signals detected

**Example:**
```
🟢 INSTITUTIONAL SIGNAL 🔥

Signal: LONG
Conviction: HIGH
Score: +9

Entry: $75,600.00
Stop Loss: $75,450.00
Target: $76,200.00
R:R Ratio: 1:4.0

Phase: ENTRY_CONFIRMED
Reason: Confirmed stop hunt with reclaim + delta flip
```

### 2. Market Overview (On-Demand)
```bash
curl -X POST http://localhost:8000/telegram/market-update
```

Shows all monitored symbols at once:
```
📊 MARKET OVERVIEW

🟢 BTCUSDT
Price: $75,688.36
Signal: MONITOR (LOW)

🟡 ETHUSDT
Price: $2,311.90
Signal: MONITOR (LOW)
```

---

## Troubleshooting

### Not Receiving Messages?

1. **Check configuration**:
   ```bash
   curl http://localhost:8000/telegram/status
   ```

2. **Verify you started the bot**:
   - Send any message to your bot in Telegram first

3. **Check logs**:
   ```bash
   tail -f logs/backend.log | grep TELEGRAM
   ```

4. **Test connectivity**:
   ```bash
   curl https://api.telegram.org
   ```

### Common Errors

| Error | Solution |
|-------|----------|
| "Chat not found" | Wrong chat ID or haven't messaged bot |
| "Bot was blocked" | Unblock the bot in Telegram |
| "Unauthorized" | Invalid bot token |
| "Not configured" | Check .env file and restart |

---

## Quick Commands

```bash
# Status check
curl http://localhost:8000/telegram/status

# Test notification
curl -X POST http://localhost:8000/telegram/test

# Market update
curl -X POST http://localhost:8000/telegram/market-update

# View logs
tail -f logs/backend.log | grep TELEGRAM
```

---

## What Triggers Notifications?

✅ **Automatic Alerts:**
- LONG signal with HIGH/MEDIUM conviction
- SHORT signal with HIGH/MEDIUM conviction
- Score ≥ 6

❌ **No Alert:**
- MONITOR signals
- FLAT/no signal
- LOW conviction (< 6 score)

---

## Need Help?

📖 Full guide: `TELEGRAM_SETUP_GUIDE.md`  
🔧 Setup script: `./setup-telegram.sh`  
📝 Logs: `tail -f logs/backend.log`
