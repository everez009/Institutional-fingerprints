# Telegram Notification Setup Guide

## Quick Setup (5 Minutes)

### Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the message: `/newbot`
3. Follow the prompts:
   - Choose a name: `Institutional Footprint Bot` (or any name you like)
   - Choose a username: Must end with `bot` (e.g., `my_footprint_bot`)
4. **Copy the bot token** - It looks like: `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`

### Step 2: Get Your Chat ID

1. Search for **@userinfobot** in Telegram
2. Send any message (e.g., `/start`)
3. It will reply with your user info
4. **Copy your ID** - It's a number like: `123456789`

Alternative method:
1. Send a message to your new bot
2. Visit: `https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates`
3. Look for `"chat":{"id":123456789}` in the response

### Step 3: Configure the System

Edit the `.env` file in `/Users/mac/institutional-footprint/`:

```bash
nano /Users/mac/institutional-footprint/.env
```

Replace these lines with your credentials:

```env
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

Save the file (Ctrl+O, Enter, Ctrl+X in nano).

### Step 4: Restart the System

```bash
cd /Users/mac/institutional-footprint
./start-all.sh restart
```

### Step 5: Test the Notification

Open your browser and visit:
```
http://localhost:8000/telegram/test
```

Or use curl:
```bash
curl -X POST http://localhost:8000/telegram/test
```

You should receive a test message on Telegram! ✅

---

## What You'll Receive

### 1. Trading Signals (Automatic)

When the system detects HIGH or MEDIUM conviction signals:

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

Time: 2024-01-15 14:30:00 UTC
```

### 2. Market Updates (On Demand)

Request a market overview:
```bash
curl -X POST http://localhost:8000/telegram/market-update
```

You'll receive:
```
📊 MARKET OVERVIEW

🟢 BTCUSDT
Price: $75,688.36
Signal: MONITOR (LOW)

🟡 ETHUSDT
Price: $2,311.90
Signal: MONITOR (LOW)

⚪ PAXGUSDT
Price: $3,245.00
Signal: FLAT (LOW)
```

### 3. System Alerts

- ✅ Configuration success
- ⚠️ Warnings
- ❌ Errors

---

## API Endpoints

### Check Status
```bash
curl http://localhost:8000/telegram/status
```

Response:
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

### Send Market Update
```bash
curl -X POST http://localhost:8000/telegram/market-update
```

---

## Troubleshooting

### Problem: "Telegram not configured"

**Solution:**
1. Check your `.env` file has correct values
2. Make sure there are no spaces around `=` sign
3. Restart the system after changes

Verify:
```bash
cat .env | grep TELEGRAM
curl http://localhost:8000/telegram/status
```

### Problem: No message received

**Possible causes:**

1. **Wrong chat ID**
   - Double-check with @userinfobot
   - Make sure you messaged your bot first

2. **Invalid bot token**
   - Verify token from @BotFather
   - Token format: `numbers:letters`

3. **Bot is blocked**
   - Make sure you haven't blocked the bot
   - Try sending a message to the bot

4. **Network issues**
   ```bash
   # Test Telegram API connectivity
   curl https://api.telegram.org
   ```

### Problem: Error messages in logs

Check backend logs:
```bash
tail -f logs/backend.log | grep TELEGRAM
```

Common errors:
- `Chat not found` → Wrong chat ID
- `Bot was blocked` → Unblock the bot
- `Unauthorized` → Invalid bot token

---

## Advanced Configuration

### Customize Notification Frequency

By default, signals are sent automatically when:
- Signal is LONG or SHORT
- Conviction is HIGH or MEDIUM

To modify this behavior, edit `engine.py`:

```python
# In the signal generation section
if signal.get("signal") in ["LONG", "SHORT"] and signal.get("conviction") in ["HIGH", "MEDIUM"]:
    await self.telegram.send_signal(signal)
```

Change to receive ALL signals:
```python
if signal.get("signal") != "FLAT":
    await self.telegram.send_signal(signal)
```

### Add Custom Alert Conditions

You can add custom notifications in `engine.py`. Example - notify on absorption detection:

```python
if absorption.get("detected") and absorption.get("duration_candles") >= 3:
    await self.telegram.send_alert(
        title="Strong Absorption Detected",
        message=f"Absorption active for {absorption['duration_candles']} candles on {self.symbol}",
        level="WARNING"
    )
```

### Multiple Chat IDs

To send to multiple recipients, modify `telegram_notifier.py`:

```python
async def _send_message(self, text: str, parse_mode: str = "HTML"):
    chat_ids = [self.chat_id, "SECOND_CHAT_ID", "THIRD_CHAT_ID"]
    
    for chat_id in chat_ids:
        # Send to each chat ID
        ...
```

---

## Security Best Practices

### 1. Protect Your Bot Token

⚠️ **Never share your bot token publicly!**

- Don't commit `.env` to Git (already in `.gitignore`)
- Don't share screenshots with token visible
- Regenerate token if compromised via @BotFather

### 2. Restrict Bot Access

Your bot can only:
- Send messages to users who started it
- Receive messages you send to it

It cannot:
- Read your other chats
- Access your contacts
- See your phone number

### 3. Use Environment Variables

Always use `.env` file instead of hardcoding credentials:

✅ **Good:**
```python
import os
token = os.getenv("TELEGRAM_BOT_TOKEN")
```

❌ **Bad:**
```python
token = "1234567890:ABCdef..."  # Never do this!
```

---

## Testing Checklist

Before going live, verify:

- [ ] Bot created via @BotFather
- [ ] Bot token copied correctly
- [ ] Chat ID obtained from @userinfobot
- [ ] `.env` file updated with credentials
- [ ] System restarted after config changes
- [ ] Test notification received successfully
- [ ] Can check status via API endpoint
- [ ] Market update sends correctly

---

## Example Workflow

### Morning Check
```bash
# Get market overview on all symbols
curl -X POST http://localhost:8000/telegram/market-update
```

### Monitor Signals
Just wait! High-conviction signals arrive automatically.

### System Health Check
```bash
# Verify Telegram is configured
curl http://localhost:8000/telegram/status

# Send test message
curl -X POST http://localhost:8000/telegram/test
```

---

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review backend logs: `tail -f logs/backend.log`
3. Verify Telegram API status: https://api.telegram.org
4. Ensure your bot isn't rate-limited (max 30 messages/second)

---

## Next Steps

Once Telegram is working:

1. ✅ Set up auto-start on boot (see main guide)
2. ✅ Configure additional symbols to monitor
3. ✅ Customize alert thresholds in `engine.py`
4. ✅ Set up log rotation for long-term operation

Happy trading! 🚀
