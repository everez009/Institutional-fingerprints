"""
Multi-Symbol Engine Manager
Manages multiple InstitutionalEntryEngine instances for simultaneous monitoring
"""

import asyncio
from typing import Dict, List
from engine import InstitutionalEntryEngine


class MultiSymbolEngine:
    def __init__(self, symbols: List[str] = None):
        self.symbols = symbols or ["BTCUSDT", "ETHUSDT", "PAXGUSDT"]
        self.engines: Dict[str, InstitutionalEntryEngine] = {}
        self.tasks: Dict[str, asyncio.Task] = {}
        
    async def start_all(self):
        """Start monitoring all symbols"""
        print(f"[MULTI-ENGINE] Starting monitoring for {len(self.symbols)} symbols: {', '.join(self.symbols)}")
        
        for symbol in self.symbols:
            await self.start_symbol(symbol)
    
    async def start_symbol(self, symbol: str):
        """Start monitoring a single symbol"""
        if symbol in self.engines:
            print(f"[MULTI-ENGINE] Symbol {symbol} already running")
            return
        
        print(f"[MULTI-ENGINE] Starting {symbol}...")
        engine = InstitutionalEntryEngine(symbol)
        self.engines[symbol] = engine
        
        # Start the engine in background
        task = asyncio.create_task(engine.run())
        self.tasks[symbol] = task
        print(f"[MULTI-ENGINE] {symbol} started successfully")
    
    async def stop_symbol(self, symbol: str):
        """Stop monitoring a symbol"""
        if symbol in self.tasks:
            self.tasks[symbol].cancel()
            del self.tasks[symbol]
        if symbol in self.engines:
            del self.engines[symbol]
        print(f"[MULTI-ENGINE] {symbol} stopped")
    
    def get_all_states(self) -> Dict:
        """Get market state for all symbols"""
        states = {}
        for symbol, engine in self.engines.items():
            try:
                states[symbol] = engine.build_market_state()
            except Exception as e:
                states[symbol] = {"error": str(e)}
        return states
    
    def get_all_signals(self) -> Dict:
        """Get latest signals for all symbols"""
        signals = {}
        for symbol, engine in self.engines.items():
            signals[symbol] = engine.latest_signal or {"signal": "FLAT", "conviction": "LOW"}
        return signals
    
    def get_summary(self) -> List[Dict]:
        """Get summary of all symbols for dashboard"""
        summary = []
        for symbol, engine in self.engines.items():
            try:
                state = engine.build_market_state()
                signal = engine.latest_signal
                
                summary.append({
                    "symbol": symbol,
                    "price": state.get("price", 0),
                    "delta": state.get("delta", 0),
                    "cumulative_delta": state.get("cumulative_delta", 0),
                    "signal": signal.get("signal", "FLAT") if signal else "FLAT",
                    "conviction": signal.get("conviction", "LOW") if signal else "LOW",
                    "score": signal.get("total_score", 0) if signal else 0,
                    "phase": signal.get("phase", "NONE") if signal else "NONE",
                    "absorption": state.get("absorption", {}).get("detected", False),
                    "iceberg": state.get("iceberg", {}).get("detected", False),
                    "stop_hunt": state.get("stop_hunt", {}).get("detected", False),
                    "divergence": state.get("divergence", "none"),
                    "spoofs_60s": state.get("spoofs_60s", 0),
                    "top_bids": state.get("top_bids", []),
                    "top_asks": state.get("top_asks", []),
                    "timestamp": state.get("timestamp", 0)
                })
            except Exception as e:
                summary.append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        return summary
