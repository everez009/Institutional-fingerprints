#!/bin/bash
# Telegram Setup Helper Script
# Guides you through setting up Telegram notifications

echo "╔═══════════════════════════════════════════════════════╗"
echo "║   Telegram Notification Setup Helper                 ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    exit 1
fi

echo "Step 1: Create a Telegram Bot"
echo "─────────────────────────────────────"
echo "1. Open Telegram and search for @BotFather"
echo "2. Send: /newbot"
echo "3. Follow the prompts to create your bot"
echo "4. Copy the bot token (looks like: 1234567890:ABCdef...)"
echo ""
read -p "Press Enter when you have your bot token... "

echo ""
echo "Enter your Bot Token:"
read -p "> " BOT_TOKEN

echo ""
echo "Step 2: Get Your Chat ID"
echo "─────────────────────────────────────"
echo "1. Search for @userinfobot in Telegram"
echo "2. Send any message (e.g., /start)"
echo "3. Copy your ID number"
echo ""
read -p "Press Enter when you have your chat ID... "

echo ""
echo "Enter your Chat ID:"
read -p "> " CHAT_ID

echo ""
echo "Step 3: Configuring..."
echo "─────────────────────────────────────"

# Backup existing .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Update .env file
sed -i.bak "s/^TELEGRAM_BOT_TOKEN=.*/TELEGRAM_BOT_TOKEN=$BOT_TOKEN/" .env
sed -i.bak "s/^TELEGRAM_CHAT_ID=.*/TELEGRAM_CHAT_ID=$CHAT_ID/" .env

# Remove backup file created by sed
rm -f .env.bak

echo "✅ Configuration saved to .env"
echo ""

# Verify configuration
echo "Verifying configuration..."
sleep 2

CONFIG_STATUS=$(curl -s http://localhost:8000/telegram/status 2>/dev/null)

if echo "$CONFIG_STATUS" | grep -q '"configured": true'; then
    echo "✅ Telegram is configured correctly!"
else
    echo "⚠️  Configuration may need verification"
    echo "Current status: $CONFIG_STATUS"
fi

echo ""
echo "Step 4: Testing..."
echo "─────────────────────────────────────"
echo "Sending test notification..."
sleep 2

TEST_RESULT=$(curl -s -X POST http://localhost:8000/telegram/test 2>/dev/null)

if echo "$TEST_RESULT" | grep -q '"status": "success"'; then
    echo "✅ Test notification sent successfully!"
    echo ""
    echo "Check your Telegram - you should have received a message."
else
    echo "❌ Test failed"
    echo "Response: $TEST_RESULT"
    echo ""
    echo "Troubleshooting:"
    echo "1. Make sure you started a conversation with your bot"
    echo "2. Verify bot token and chat ID are correct"
    echo "3. Check that the backend is running on port 8000"
fi

echo ""
echo "═══════════════════════════════════════════════════════"
echo "Setup Complete!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "Useful commands:"
echo "  • Check status: curl http://localhost:8000/telegram/status"
echo "  • Send test:    curl -X POST http://localhost:8000/telegram/test"
echo "  • Market update: curl -X POST http://localhost:8000/telegram/market-update"
echo ""
echo "For more information, see TELEGRAM_SETUP_GUIDE.md"
echo ""
