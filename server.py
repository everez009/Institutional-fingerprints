"""
FastAPI Server — Institutional Entry Detection System
Serves market state and signals to the React frontend via REST + WebSocket
Supports 24/7 operation with auto-reconnect and health monitoring
"""

import asyncio
import json
import time
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from engine import InstitutionalEntryEngine
from multi_engine import MultiSymbolEngine

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
    return JSONResponse(engine.build_market_state())


@app.get("/signal")
async def get_latest_signal():
    return JSONResponse(engine.latest_signal or {"signal": "FLAT", "conviction": "LOW"})


@app.get("/signals/history")
async def get_signal_history():
    return JSONResponse(list(engine.signal_history))


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
    """Switch trading symbol"""
    global engine
    symbol = request.get("symbol", "BTCUSDT").upper()
    
    if symbol not in ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "XAUUSDT"]:
        return JSONResponse({"error": "Unsupported symbol"}, status_code=400)
    
    # Stop old engine
    print(f"[SERVER] Switching from {engine.symbol.upper()} to {symbol}")
    
    # Create new engine with new symbol
    engine = InstitutionalEntryEngine(symbol)
    engine.on_market_update = on_market_update
    engine.on_signal = on_signal
    
    # Restart engine
    asyncio.create_task(engine.run())
    
    return JSONResponse({"status": "success", "symbol": symbol})


@app.get("/symbols")
async def get_symbols():
    """Get supported symbols"""
    return JSONResponse({
        "current": list(multi_engine.engines.keys()) if multi_engine.engines else [],
        "supported": ["BTCUSDT", "ETHUSDT", "PAXGUSDT", "XAUUSDT"]
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
