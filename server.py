"""
FastAPI Server — Institutional Entry Detection System
Serves market state and signals to the React frontend via REST + WebSocket
Supports 24/7 operation with auto-reconnect and health monitoring
"""

import asyncio
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from engine import InstitutionalEntryEngine
from multi_engine import MultiSymbolEngine
from telegram_notifier import TelegramNotifier

app = FastAPI(title="Institutional Entry Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
# Option 1: Single symbol (commented out)
# engine = InstitutionalEntryEngine("BTCUSDT")

# Option 2: Multi-symbol monitoring (active)
multi_engine = MultiSymbolEngine(["BTCUSDT", "ETHUSDT", "PAXGUSDT"])

# For backward compatibility, create a default engine
engine = InstitutionalEntryEngine("BTCUSDT")

# Telegram notifier instance
telegram = TelegramNotifier()

connected_clients: list[WebSocket] = []


# ─────────────────────────────────────────────
# WEBSOCKET BROADCAST
# ─────────────────────────────────────────────

async def broadcast(data: dict):
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


async def on_market_update(state: dict):
    await broadcast({"type": "market_update", "data": state})


async def on_signal(signal: dict):
    await broadcast({"type": "signal", "data": signal})


engine.on_market_update = on_market_update
engine.on_signal = on_signal


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/state")
async def get_state():
    """Get market state for current symbol"""
    # Get current symbol from single engine
    current_symbol = engine.symbol.upper()
    
    # Try to get data from multi-engine for the current symbol
    try:
        summary = multi_engine.get_summary()
        symbol_data = next((s for s in summary if s['symbol'] == current_symbol), None)
        if symbol_data and symbol_data.get('price', 0) > 0:
            # Return multi-engine data formatted for single-symbol view
            return JSONResponse({
                "price": symbol_data['price'],
                "delta": symbol_data.get('delta', 0),
                "cumulative_delta": symbol_data.get('cumulative_delta', 0),
                "absorption": {"detected": symbol_data.get('absorption', False)},
                "iceberg": {"detected": symbol_data.get('iceberg', False)},
                "stop_hunt": {"detected": symbol_data.get('stop_hunt', False)},
                "divergence": symbol_data.get('divergence', 'none'),
                "spoofs_60s": symbol_data.get('spoofs_60s', 0),
                "top_bids": symbol_data.get('top_bids', []),
                "top_asks": symbol_data.get('top_asks', []),
                "phase": {
                    "absorption_active": symbol_data.get('absorption', False),
                    "stop_hunt_occurred": symbol_data.get('stop_hunt', False),
                    "delta_confirmed": False,
                    "reclaim_confirmed": False
                },
                "latest_signal": {
                    "signal": symbol_data.get('signal', 'FLAT'),
                    "conviction": symbol_data.get('conviction', 'LOW'),
                    "total_score": symbol_data.get('score', 0),
                    "phase": symbol_data.get('phase', 'NONE')
                },
                "timestamp": symbol_data.get('timestamp', time.time())
            })
    except Exception as e:
        print(f"[ERROR] Getting state from multi-engine: {e}")
    
    # Fallback to single engine (will be empty if not running)
    return JSONResponse(engine.build_market_state())


@app.get("/signal")
async def get_latest_signal():
    """Get latest signal for default symbol (BTCUSDT from multi-engine)"""
    try:
        summary = multi_engine.get_summary()
        btc_data = next((s for s in summary if s['symbol'] == 'BTCUSDT'), None)
        if btc_data:
            return JSONResponse({
                "signal": btc_data.get('signal', 'FLAT'),
                "conviction": btc_data.get('conviction', 'LOW'),
                "total_score": btc_data.get('score', 0),
                "phase": btc_data.get('phase', 'NONE')
            })
    except Exception as e:
        print(f"[ERROR] Getting signal from multi-engine: {e}")
    
    return JSONResponse(engine.latest_signal or {"signal": "FLAT", "conviction": "LOW"})


@app.get("/signals/history")
async def get_signal_history():
    """Get signal history - returns recent signals from multi-engine BTCUSDT"""
    # For now, return empty array since we're using multi-engine
    # In future, could store history per symbol
    return JSONResponse(list(engine.signal_history)[-20:])  # Last 20 signals


@app.get("/payload")
async def get_payload():
    return JSONResponse(engine.build_payload())


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": time.time(),
        "symbol": engine.symbol.upper(),
        "price": engine.current_price,
        "signals_generated": len(engine.signal_history)
    })


@app.post("/telegram/test")
async def test_telegram():
    """Test Telegram notification"""
    try:
        await engine.telegram.send_alert(
            "Test Notification",
            "Telegram integration is working correctly! ✅",
            "SUCCESS"
        )
        return JSONResponse({"status": "success", "message": "Test message sent"})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/signal/force")
async def force_signal():
    """Manually trigger signal generation (rule-based, no LLM)"""
    try:
        # Generate signal using rule-based logic
        signal = engine.generate_signal()
        signal["payload"] = engine.build_payload()
        engine.latest_signal = signal
        engine.signal_history.appendleft(signal)
        await on_signal(signal)
        
        # Send Telegram notification if significant
        if signal.get("signal") in ["LONG", "SHORT"]:
            await engine.telegram.send_signal(signal)
        
        return JSONResponse(signal)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/symbol/switch")
async def switch_symbol(request: dict):
    """Switch trading symbol - updates single engine symbol for API consistency"""
    global engine
    symbol = request.get("symbol", "BTCUSDT").upper()
    
    if symbol not in ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "XAUUSDT"]:
        return JSONResponse({"error": "Unsupported symbol"}, status_code=400)
    
    # Just update the single engine's symbol (don't restart it - multi-engine has the data)
    print(f"[SERVER] Switching view to {symbol}")
    
    # Create a new engine instance with just the symbol changed (for API state)
    engine = InstitutionalEntryEngine(symbol)
    
    return JSONResponse({"status": "success", "symbol": symbol})


@app.get("/symbols")
async def get_symbols():
    """Get supported symbols and current symbol"""
    current_symbol = engine.symbol.upper() if engine else "BTCUSDT"
    supported = ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "XAUUSDT"]
    
    return JSONResponse({
        "current": current_symbol,
        "all": supported,  # All available symbols
        "supported": supported,
        "active_multi": list(multi_engine.engines.keys()) if multi_engine.engines else []
    })


@app.get("/multi/state")
async def get_multi_state():
    """Get market state for all monitored symbols"""
    return JSONResponse(multi_engine.get_all_states())


@app.get("/multi/signals")
async def get_multi_signals():
    """Get latest signals for all monitored symbols"""
    return JSONResponse(multi_engine.get_all_signals())


@app.get("/multi/summary")
async def get_multi_summary():
    """Get summary of all symbols for dashboard"""
    return JSONResponse(multi_engine.get_summary())


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        # Send current state immediately on connect
        await websocket.send_json({"type": "market_update", "data": engine.build_market_state()})
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)


# ─────────────────────────────────────────────
# TELEGRAM NOTIFICATIONS
# ─────────────────────────────────────────────

@app.post("/telegram/test")
async def test_telegram():
    """Send a test notification to Telegram"""
    if not telegram.is_configured():
        return JSONResponse(
            {"error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file"},
            status_code=400
        )
    
    try:
        success = await telegram.send_alert(
            title="Test Notification",
            message="Your Institutional Footprint Detection System is working correctly! 🎉\n\nYou will receive alerts for:\n• LONG/SHORT signals\n• HIGH/MEDIUM conviction trades\n• Market updates",
            level="SUCCESS"
        )
        
        if success:
            return JSONResponse({"status": "success", "message": "Test notification sent successfully!"})
        else:
            return JSONResponse({"error": "Failed to send message"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/telegram/status")
async def telegram_status():
    """Check Telegram configuration status"""
    return JSONResponse({
        "configured": telegram.is_configured(),
        "bot_token_set": bool(telegram.bot_token),
        "chat_id_set": bool(telegram.chat_id)
    })


@app.post("/alert/telegram")
async def send_dashboard_alert(request: dict):
    """Send alert from dashboard to Telegram"""
    if not telegram.is_configured():
        return JSONResponse(
            {"error": "Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env file"},
            status_code=400
        )
    
    try:
        signal = request.get("signal", "UNKNOWN")
        conviction = request.get("conviction", "LOW")
        score = request.get("score", 0)
        symbol = request.get("symbol", "BTCUSDT")
        timestamp = request.get("timestamp", "")
        
        # Format emoji
        emoji = {
            "LONG": "🟢",
            "SHORT": "🔴",
            "MONITOR": "🟡"
        }.get(signal, "⚪")
        
        conviction_emoji = {
            "HIGH": "🔥",
            "MEDIUM": "⚡",
            "LOW": "💤"
        }.get(conviction, "")
        
        message = f"""
{emoji} *DASHBOARD ALERT* {conviction_emoji}

*Symbol:* {symbol}
*Signal:* {signal}
*Conviction:* {conviction}
*Score:* {score:+d}

_Time: {timestamp}_
        """.strip()
        
        success = await telegram._send_message(message, parse_mode="Markdown")
        
        if success:
            return JSONResponse({"status": "success", "message": "Telegram alert sent"})
        else:
            return JSONResponse({"error": "Failed to send Telegram message"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/telegram/market-update")
async def send_market_update():
    """Send current market state via Telegram"""
    if not telegram.is_configured():
        return JSONResponse(
            {"error": "Telegram not configured"},
            status_code=400
        )
    
    try:
        # Get multi-symbol summary
        summary = multi_engine.get_summary()
        
        message = "📊 *MARKET OVERVIEW*\n\n"
        for sym_data in summary:
            symbol = sym_data.get('symbol', 'UNKNOWN')
            price = sym_data.get('price', 0)
            signal = sym_data.get('signal', 'FLAT')
            conviction = sym_data.get('conviction', 'LOW')
            
            emoji = {"LONG": "🟢", "SHORT": "🔴", "MONITOR": "🟡"}.get(signal, "⚪")
            message += f"{emoji} *{symbol}*\n"
            message += f"Price: ${price:,.2f}\n"
            message += f"Signal: {signal} ({conviction})\n\n"
        
        success = await telegram._send_message(message, parse_mode="Markdown")
        
        if success:
            return JSONResponse({"status": "success", "message": "Market update sent!"})
        else:
            return JSONResponse({"error": "Failed to send"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─────────────────────────────────────────────
# XAUUSD SMART MONEY CONCEPTS (SMC) ENDPOINTS
# ─────────────────────────────────────────────

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
            return {"status": "pending", "message": "No data available yet. Monitor may be starting."}
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


# ─────────────────────────────────────────────
# STARTUP
# ─────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    print("[SERVER] Starting multi-symbol engine...")
    try:
        # Start all symbol engines
        asyncio.create_task(multi_engine.start_all())
        print(f"[SERVER] Multi-symbol engine started with {len(multi_engine.symbols)} symbols")
    except Exception as e:
        print(f"[SERVER] Error starting engine: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
