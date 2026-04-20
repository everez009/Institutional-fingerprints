"""
Institutional Entry Detection Engine
Connects to Binance WebSocket, processes order flow data,
detects institutional fingerprints, and generates signals based on rule-based logic.
NO LLM REQUIRED - All signals generated from detected market conditions.
"""

import asyncio
import json
import time
import websockets
import aiohttp
from collections import deque, defaultdict
from dataclasses import dataclass, asdict, field
from typing import Optional
import statistics
from volume_profile import VolumeProfileCalculator, SESSION_CANDLES
from telegram_notifier import TelegramNotifier


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

SYMBOL = "BTCUSDT"
BINANCE_WS_BASE = "wss://stream.binance.com:9443/ws"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY"  # Replace with your key
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# Thresholds
LARGE_WALL_THRESHOLD = 50.0          # BTC — adjust per asset
SPOOF_MAX_AGE_MS = 5000
SPOOF_MIN_SIZE_RATIO = 15
ICEBERG_MIN_REFRESHES = 5
ABSORPTION_MAX_PRICE_MOVE_PCT = 0.05
VOLUME_SPIKE_RATIO = 3.0
DELTA_DIVERGENCE_CANDLES = 3
CANDLE_TIMEFRAME_SECONDS = 300       # 5 min candles

# Signal Generation Thresholds (Rule-Based)
MIN_CONVICTION_SCORE = 6             # Minimum score to generate signal
HIGH_CONVICTION_SCORE = 9            # Score threshold for HIGH conviction
MEDIUM_CONVICTION_SCORE = 6          # Score threshold for MEDIUM conviction


# ─────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class Wall:
    price: float
    size: float
    first_seen: float
    last_seen: float
    peak_size: float
    refresh_count: int = 0
    fills: float = 0.0
    appeared_after_sweep: bool = False
    cancelled: bool = False
    cancel_time: Optional[float] = None
    price_at_appearance: float = 0.0
    confidence: str = "real"  # real | suspicious | spoof


@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float
    buy_volume: float
    sell_volume: float
    delta: float
    timestamp: float
    pattern: str = "none"


@dataclass
class PhaseTracker:
    absorption_phase_active: bool = False
    absorption_candles: int = 0
    stop_hunt_occurred: bool = False
    stop_hunt_candles_ago: int = 0
    stop_hunt_level: float = 0.0
    delta_confirmed: bool = False
    reclaim_confirmed: bool = False
    last_swing_low: float = 0.0
    last_swing_high: float = 0.0


# ─────────────────────────────────────────────
# CORE ENGINE
# ─────────────────────────────────────────────

class InstitutionalEntryEngine:

    def __init__(self, symbol: str = SYMBOL):
        self.symbol = symbol.lower()

        # Market state
        self.current_price = 0.0
        self.mid_price = 0.0

        # Order book state
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.bid_walls: dict[float, Wall] = {}
        self.ask_walls: dict[float, Wall] = {}

        # Trade history
        self.trades_1m: deque = deque(maxlen=500)
        self.volume_history: deque = deque(maxlen=100)

        # Candle state
        self.current_candle: Optional[Candle] = None
        self.candle_history: deque = deque(maxlen=50)
        self.candle_start_time: float = 0.0

        # Footprint / delta
        self.cumulative_delta: float = 0.0
        self.cumulative_delta_history: deque = deque(maxlen=20)

        # Spoof tracking
        self.spoof_log: list = []
        self.cancelled_walls: list = []

        # Phase tracking
        self.phase = PhaseTracker()

        # Volume profile
        self.vp = VolumeProfileCalculator()
        self.session_candle_count: int = 0

        # Signal output (for UI polling)
        self.latest_signal: dict = {}
        self.signal_history: deque = deque(maxlen=100)

        # Callbacks for UI
        self.on_signal = None
        self.on_market_update = None
        
        # Telegram notifier
        self.telegram = TelegramNotifier()

    # ─────────────────────────────────────────
    # ORDER BOOK PROCESSING
    # ─────────────────────────────────────────

    def process_depth_update(self, data: dict):
        now = time.time() * 1000

        for bid in data.get("b", []):
            price, qty = float(bid[0]), float(bid[1])
            if qty == 0:
                self._handle_wall_removal("bid", price, now)
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty
                self._track_wall("bid", price, qty, now)

        for ask in data.get("a", []):
            price, qty = float(ask[0]), float(ask[1])
            if qty == 0:
                self._handle_wall_removal("ask", price, now)
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty
                self._track_wall("ask", price, qty, now)

        self._update_mid()

    def _track_wall(self, side: str, price: float, qty: float, now: float):
        walls = self.bid_walls if side == "bid" else self.ask_walls
        avg_nearby = self._avg_nearby_depth(side, price)

        if qty >= LARGE_WALL_THRESHOLD or (avg_nearby > 0 and qty / avg_nearby >= SPOOF_MIN_SIZE_RATIO):
            if price not in walls:
                walls[price] = Wall(
                    price=price,
                    size=qty,
                    first_seen=now,
                    last_seen=now,
                    peak_size=qty,
                    price_at_appearance=self.mid_price,
                    appeared_after_sweep=self.phase.stop_hunt_occurred and self.phase.stop_hunt_candles_ago <= 3
                )
            else:
                wall = walls[price]
                if qty < wall.size:
                    wall.fills += (wall.size - qty)
                    wall.refresh_count += 1
                wall.size = qty
                wall.last_seen = now
                wall.peak_size = max(wall.peak_size, qty)
                wall.confidence = self._assess_wall_confidence(wall, now)

    def _handle_wall_removal(self, side: str, price: float, now: float):
        walls = self.bid_walls if side == "bid" else self.ask_walls
        if price in walls:
            wall = walls[price]
            age = now - wall.first_seen
            price_moved_toward = (
                (side == "bid" and self.mid_price < wall.price_at_appearance) or
                (side == "ask" and self.mid_price > wall.price_at_appearance)
            )
            no_fills = wall.fills < wall.peak_size * 0.1

            if age < SPOOF_MAX_AGE_MS and price_moved_toward and no_fills:
                wall.confidence = "spoof"
                wall.cancelled = True
                wall.cancel_time = now
                self.spoof_log.append({
                    "side": side,
                    "price": price,
                    "size": wall.peak_size,
                    "age_ms": age,
                    "time": now
                })
            self.cancelled_walls.append(walls.pop(price))

    def _assess_wall_confidence(self, wall: Wall, now: float) -> str:
        age = now - wall.first_seen
        avg_nearby = self._avg_nearby_depth(
            "bid" if wall in self.bid_walls.values() else "ask", wall.price
        )
        size_ratio = wall.peak_size / avg_nearby if avg_nearby > 0 else 0

        spoof_count = sum(
            1 for s in self.spoof_log
            if s["price"] == wall.price and now - s["time"] < 60000
        )

        if spoof_count >= 3:
            return "spoof"
        if age < 2000 and size_ratio > SPOOF_MIN_SIZE_RATIO:
            return "suspicious"
        if wall.refresh_count >= ICEBERG_MIN_REFRESHES:
            return "real"  # Iceberg — definitely real
        return "real"

    def _avg_nearby_depth(self, side: str, price: float) -> float:
        book = self.bids if side == "bid" else self.asks
        nearby = [v for p, v in book.items() if abs(p - price) / price < 0.002]
        return statistics.mean(nearby) if nearby else 1.0

    def _update_mid(self):
        best_bid = max(self.bids.keys(), default=0)
        best_ask = min(self.asks.keys(), default=0)
        if best_bid and best_ask:
            self.mid_price = (best_bid + best_ask) / 2

    # ─────────────────────────────────────────
    # TRADE PROCESSING
    # ─────────────────────────────────────────

    def process_trade(self, data: dict):
        now = time.time() * 1000
        price = float(data["p"])
        qty = float(data["q"])
        is_buyer_maker = data["m"]  # True = seller aggressive, False = buyer aggressive

        side = "sell" if is_buyer_maker else "buy"
        self.current_price = price

        trade = {
            "price": price,
            "qty": qty,
            "side": side,
            "timestamp": now
        }
        self.trades_1m.append(trade)

        # Update current candle
        self._update_candle(price, qty, side, now)

        # Update cumulative delta
        delta_contribution = qty if side == "buy" else -qty
        self.cumulative_delta += delta_contribution

        # Check fills against walls
        self._check_wall_fills(price, qty, side)

        # Feed volume profile
        self.vp.add_trade(price, qty, now)

    def _check_wall_fills(self, price: float, qty: float, side: str):
        # If aggressive sell hitting bid wall — check absorption
        if side == "sell" and price in self.bid_walls:
            self.bid_walls[price].fills += qty
        if side == "buy" and price in self.ask_walls:
            self.ask_walls[price].fills += qty

    def _update_candle(self, price: float, qty: float, side: str, now: float):
        candle_bucket = int(now / 1000 / CANDLE_TIMEFRAME_SECONDS) * CANDLE_TIMEFRAME_SECONDS

        if self.current_candle is None or self.candle_start_time != candle_bucket:
            if self.current_candle:
                self.current_candle.pattern = self._detect_candle_pattern(self.current_candle)
                self.candle_history.append(self.current_candle)
                self.cumulative_delta_history.append(self.cumulative_delta)

                # Session management for volume profile
                self.session_candle_count += 1
                if self.session_candle_count >= SESSION_CANDLES:
                    self.vp.new_session()
                    self.session_candle_count = 0

            self.current_candle = Candle(
                open=price, high=price, low=price, close=price,
                volume=qty, buy_volume=qty if side == "buy" else 0,
                sell_volume=qty if side == "sell" else 0,
                delta=qty if side == "buy" else -qty,
                timestamp=candle_bucket
            )
            self.candle_start_time = candle_bucket
        else:
            c = self.current_candle
            c.high = max(c.high, price)
            c.low = min(c.low, price)
            c.close = price
            c.volume += qty
            if side == "buy":
                c.buy_volume += qty
            else:
                c.sell_volume += qty
            c.delta = c.buy_volume - c.sell_volume

    def _detect_candle_pattern(self, c: Candle) -> str:
        body = abs(c.close - c.open)
        total_range = c.high - c.low
        if total_range == 0:
            return "none"
        upper_wick = c.high - max(c.open, c.close)
        lower_wick = min(c.open, c.close) - c.low
        body_pct = body / total_range

        if body_pct < 0.1:
            return "doji"
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            return "hammer"
        if upper_wick > body * 2 and lower_wick < body * 0.5:
            return "shooting_star"
        if c.close > c.open and body_pct > 0.6:
            return "engulfing_bull"
        if c.close < c.open and body_pct > 0.6:
            return "engulfing_bear"
        return "none"

    # ─────────────────────────────────────────
    # FINGERPRINT DETECTION
    # ─────────────────────────────────────────

    def detect_absorption(self) -> dict:
        if not self.current_candle or self.current_candle.volume == 0:
            return {"detected": False, "side": "none", "duration_candles": 0}

        c = self.current_candle
        price_move_pct = abs(c.close - c.open) / c.open * 100
        large_volume = c.volume > self._avg_candle_volume() * 2

        if large_volume and price_move_pct < ABSORPTION_MAX_PRICE_MOVE_PCT:
            side = "sell" if c.sell_volume > c.buy_volume else "buy"
            duration = self._count_absorption_candles(side)
            return {
                "detected": True,
                "side": side,
                "duration_candles": duration,
                "volume": c.volume,
                "price_move_pct": price_move_pct
            }
        return {"detected": False, "side": "none", "duration_candles": 0}

    def _count_absorption_candles(self, side: str) -> int:
        count = 1
        for c in reversed(list(self.candle_history)):
            price_move = abs(c.close - c.open) / c.open * 100
            dominant = "sell" if c.sell_volume > c.buy_volume else "buy"
            if dominant == side and price_move < ABSORPTION_MAX_PRICE_MOVE_PCT:
                count += 1
            else:
                break
        return count

    def _avg_candle_volume(self) -> float:
        vols = [c.volume for c in self.candle_history]
        return statistics.mean(vols) if vols else 1.0

    def detect_iceberg(self) -> dict:
        icebergs = []
        for side, walls in [("bid", self.bid_walls), ("ask", self.ask_walls)]:
            for price, wall in walls.items():
                if wall.refresh_count >= ICEBERG_MIN_REFRESHES:
                    estimated_true = wall.fills + wall.size
                    icebergs.append({
                        "side": side,
                        "price": price,
                        "visible_size": wall.size,
                        "estimated_true_size": estimated_true,
                        "refresh_count": wall.refresh_count,
                        "confidence": wall.confidence
                    })
        if icebergs:
            best = max(icebergs, key=lambda x: x["refresh_count"])
            return {"detected": True, **best}
        return {"detected": False, "side": "none", "refresh_count": 0,
                "visible_size": 0, "estimated_true_size": 0, "price": 0}

    def detect_stop_hunt(self) -> dict:
        if len(self.candle_history) < 3:
            return {"detected": False, "direction": "none", "confirmed": False}

        candles = list(self.candle_history)
        recent = candles[-1]
        avg_vol = self._avg_candle_volume()
        swing_low = self.phase.last_swing_low
        swing_high = self.phase.last_swing_high

        # Long stop hunt — swept below swing low
        if swing_low > 0 and recent.low < swing_low:
            volume_spike = recent.volume / avg_vol if avg_vol > 0 else 0
            reclaimed = recent.close > swing_low
            delta_flipped = recent.delta > 0 and (
                len(candles) >= 2 and candles[-2].delta < 0
            )
            bid_wall_post_sweep = any(
                w.appeared_after_sweep for w in self.bid_walls.values()
            )

            if volume_spike >= VOLUME_SPIKE_RATIO:
                self.phase.stop_hunt_occurred = True
                self.phase.stop_hunt_level = swing_low
                self.phase.reclaim_confirmed = reclaimed
                self.phase.delta_confirmed = delta_flipped

                return {
                    "detected": True,
                    "direction": "long_stop_hunt",
                    "swept_level": swing_low,
                    "sweep_wick_size_pct": abs(recent.low - swing_low) / swing_low * 100,
                    "volume_spike_ratio": round(volume_spike, 2),
                    "price_reclaimed": reclaimed,
                    "reclaim_candles": 1 if reclaimed else 0,
                    "bid_wall_post_sweep": bid_wall_post_sweep,
                    "confirmed": reclaimed and delta_flipped
                }

        # Short stop hunt — swept above swing high
        if swing_high > 0 and recent.high > swing_high:
            volume_spike = recent.volume / avg_vol if avg_vol > 0 else 0
            reclaimed = recent.close < swing_high
            delta_flipped = recent.delta < 0 and (
                len(candles) >= 2 and candles[-2].delta > 0
            )

            if volume_spike >= VOLUME_SPIKE_RATIO:
                self.phase.stop_hunt_occurred = True
                self.phase.stop_hunt_level = swing_high
                return {
                    "detected": True,
                    "direction": "short_stop_hunt",
                    "swept_level": swing_high,
                    "sweep_wick_size_pct": abs(recent.high - swing_high) / swing_high * 100,
                    "volume_spike_ratio": round(volume_spike, 2),
                    "price_reclaimed": reclaimed,
                    "reclaim_candles": 1 if reclaimed else 0,
                    "bid_wall_post_sweep": False,
                    "confirmed": reclaimed and delta_flipped
                }

        return {"detected": False, "direction": "none", "confirmed": False,
                "swept_level": 0, "volume_spike_ratio": 0, "price_reclaimed": False}

    def detect_delta_divergence(self) -> str:
        if len(self.candle_history) < DELTA_DIVERGENCE_CANDLES:
            return "none"
        candles = list(self.candle_history)[-DELTA_DIVERGENCE_CANDLES:]
        deltas = list(self.cumulative_delta_history)[-DELTA_DIVERGENCE_CANDLES:]

        if len(deltas) < DELTA_DIVERGENCE_CANDLES:
            return "none"

        price_lower_low = candles[-1].low < candles[0].low
        delta_higher_low = deltas[-1] > deltas[0]
        if price_lower_low and delta_higher_low:
            return "bullish"

        price_higher_high = candles[-1].high > candles[0].high
        delta_lower_high = deltas[-1] < deltas[0]
        if price_higher_high and delta_lower_high:
            return "bearish"

        return "none"

    def detect_volume_spike(self) -> dict:
        if not self.current_candle:
            return {"detected": False, "ratio": 0, "price_move_pct": 0}
        avg = self._avg_candle_volume()
        ratio = self.current_candle.volume / avg if avg > 0 else 0
        price_move = abs(self.current_candle.close - self.current_candle.open) / self.current_candle.open * 100
        detected = ratio >= VOLUME_SPIKE_RATIO
        return {"detected": detected, "ratio": round(ratio, 2), "price_move_pct": round(price_move, 4)}

    def update_swing_levels(self):
        if len(self.candle_history) < 5:
            return
        candles = list(self.candle_history)
        lows = [c.low for c in candles[-5:]]
        highs = [c.high for c in candles[-5:]]
        self.phase.last_swing_low = min(lows)
        self.phase.last_swing_high = max(highs)

    # ─────────────────────────────────────────
    # PAYLOAD BUILDER
    # ─────────────────────────────────────────

    def build_payload(self) -> dict:
        self.update_swing_levels()
        now = time.time() * 1000

        c = self.current_candle
        absorption = self.detect_absorption()
        iceberg = self.detect_iceberg()
        stop_hunt = self.detect_stop_hunt()
        divergence = self.detect_delta_divergence()
        vol_spike = self.detect_volume_spike()

        recent_trades_1m = [t for t in self.trades_1m if now - t["timestamp"] < 60000]
        agg_buy = sum(t["qty"] for t in recent_trades_1m if t["side"] == "buy")
        agg_sell = sum(t["qty"] for t in recent_trades_1m if t["side"] == "sell")
        large_trades = [t for t in recent_trades_1m if t["qty"] > LARGE_WALL_THRESHOLD * 0.1]

        recent_spoofs = [s for s in self.spoof_log if now - s["time"] < 60000]
        dominant_spoof = "bid" if sum(1 for s in recent_spoofs if s["side"] == "bid") > len(recent_spoofs) / 2 else "ask" if recent_spoofs else "none"

        real_bid_walls = [
            {"price": w.price, "size": w.size, "age_ms": int(now - w.first_seen),
             "appeared_after_sweep": w.appeared_after_sweep, "confidence": w.confidence}
            for w in sorted(self.bid_walls.values(), key=lambda x: -x.size)[:5]
            if w.confidence != "spoof"
        ]
        real_ask_walls = [
            {"price": w.price, "size": w.size, "age_ms": int(now - w.first_seen),
             "appeared_after_sweep": w.appeared_after_sweep, "confidence": w.confidence}
            for w in sorted(self.ask_walls.values(), key=lambda x: -x.size)[:5]
            if w.confidence != "spoof"
        ]

        total_bids = sum(self.bids.values())
        total_asks = sum(self.asks.values())
        book_ratio = total_bids / total_asks if total_asks > 0 else 1.0

        candle_data = {}
        if c:
            total = c.high - c.low if c.high != c.low else 1
            candle_data = {
                "timeframe": "5m",
                "open": c.open, "high": c.high, "low": c.low, "close": c.close,
                "body_size_pct": round(abs(c.close - c.open) / total * 100, 2),
                "upper_wick_pct": round((c.high - max(c.open, c.close)) / total * 100, 2),
                "lower_wick_pct": round((min(c.open, c.close) - c.low) / total * 100, 2),
                "pattern": c.pattern
            }

        cum_delta_list = list(self.cumulative_delta_history)
        cum_delta_trend = "flat"
        if len(cum_delta_list) >= 3:
            if cum_delta_list[-1] > cum_delta_list[-3]:
                cum_delta_trend = "rising"
            elif cum_delta_list[-1] < cum_delta_list[-3]:
                cum_delta_trend = "falling"

        delta_flipped = False
        delta_flip_candles_ago = 0
        if len(self.candle_history) >= 2:
            candles = list(self.candle_history)
            if candles[-1].delta > 0 and candles[-2].delta < 0:
                delta_flipped = True
                delta_flip_candles_ago = 1
            elif len(candles) >= 3 and candles[-1].delta > 0 and candles[-3].delta < 0:
                delta_flipped = True
                delta_flip_candles_ago = 2

        return {
            "symbol": self.symbol.upper(),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "price": {
                "current": self.current_price,
                "change_1m": 0.0,
                "change_5m": 0.0,
                "change_15m": 0.0
            },
            "candlestick": candle_data,
            "footprint": {
                "delta": round(c.delta if c else 0, 4),
                "cumulative_delta": round(self.cumulative_delta, 4),
                "cumulative_delta_trend": cum_delta_trend,
                "delta_divergence": divergence,
                "delta_flipped": delta_flipped,
                "delta_flip_candles_ago": delta_flip_candles_ago,
                "dominant_side": "buy" if (c and c.buy_volume > c.sell_volume) else "sell",
                "absorption_detected": absorption["detected"],
                "absorption_side": absorption.get("side", "none"),
                "absorption_duration_candles": absorption.get("duration_candles", 0),
                "sell_delta_spike": bool(c and c.delta < -LARGE_WALL_THRESHOLD * 2),
                "buy_delta_spike": bool(c and c.delta > LARGE_WALL_THRESHOLD * 2)
            },
            "volume_profile": self.vp.to_payload(self.current_price),
            "order_book": {
                "bid_walls": real_bid_walls,
                "ask_walls": real_ask_walls,
                "thin_book_above": len([p for p in self.asks if p > self.current_price * 1.002]) < 5,
                "thin_book_below": len([p for p in self.bids if p < self.current_price * 0.998]) < 5,
                "book_imbalance_ratio": round(book_ratio, 3)
            },
            "stop_hunt": stop_hunt,
            "iceberg": iceberg,
            "trade_prints": {
                "large_trades_1m": large_trades[-10:],
                "aggressive_buy_volume_1m": round(agg_buy, 4),
                "aggressive_sell_volume_1m": round(agg_sell, 4),
                "buy_sell_ratio": round(agg_buy / agg_sell if agg_sell > 0 else 1.0, 3),
                "volume_spike_detected": vol_spike["detected"],
                "volume_spike_ratio": vol_spike["ratio"],
                "price_movement_on_spike_pct": vol_spike["price_move_pct"],
                "iceberg_detected": iceberg["detected"],
                "iceberg_side": iceberg.get("side", "none")
            },
            "spoof_detector": {
                "active_spoofs": [s for s in self.spoof_log if now - s["time"] < 10000],
                "recent_spoofs_60s": len(recent_spoofs),
                "dominant_spoof_side": dominant_spoof,
                "spoof_signal": "bull_trap" if dominant_spoof == "bid" else "bear_trap" if dominant_spoof == "ask" else "none"
            },
            "phase_tracker": {
                "absorption_phase_active": absorption["detected"],
                "absorption_candles": absorption.get("duration_candles", 0),
                "stop_hunt_occurred": self.phase.stop_hunt_occurred,
                "stop_hunt_candles_ago": self.phase.stop_hunt_candles_ago,
                "delta_confirmed": self.phase.delta_confirmed,
                "reclaim_confirmed": self.phase.reclaim_confirmed
            }
        }

    # ─────────────────────────────────────────
    # RULE-BASED SIGNAL GENERATION
    # ─────────────────────────────────────────

    def generate_signal(self) -> dict:
        """
        Generate trading signal based on detected institutional conditions.
        NO LLM required - uses scoring system based on fingerprint detection.
        """
        self.update_swing_levels()
        
        # Detect all fingerprints
        absorption = self.detect_absorption()
        iceberg = self.detect_iceberg()
        stop_hunt = self.detect_stop_hunt()
        divergence = self.detect_delta_divergence()
        vol_spike = self.detect_volume_spike()
        
        # Calculate conviction score
        score = 0
        reasons = []
        conflicts = []
        warnings = []
        
        # Phase tracking
        phase = "NONE"
        
        # Score: Absorption (max +3)
        if absorption.get("detected"):
            duration = absorption.get("duration_candles", 0)
            if duration >= 3:
                score += 3
                reasons.append(f"Strong absorption ({duration} candles)")
            elif duration >= 2:
                score += 2
                reasons.append(f"Moderate absorption ({duration} candles)")
            else:
                score += 1
                reasons.append("Weak absorption detected")
        
        # Score: Iceberg orders (max +2)
        if iceberg.get("detected"):
            refreshes = iceberg.get("refresh_count", 0)
            if refreshes >= 8:
                score += 2
                reasons.append(f"Large iceberg ({refreshes} refreshes)")
            else:
                score += 1
                reasons.append(f"Iceberg detected ({refreshes} refreshes)")
        
        # Score: Stop hunt (max +4) - KEY SIGNAL
        if stop_hunt.get("detected"):
            if stop_hunt.get("confirmed"):
                score += 4
                reasons.append("Confirmed stop hunt with reclaim + delta flip")
                phase = "ENTRY_CONFIRMED"
            elif stop_hunt.get("price_reclaimed"):
                score += 3
                reasons.append("Stop hunt with price reclaim")
                phase = "STOP_HUNT"
            else:
                score += 2
                reasons.append("Stop hunt detected (waiting for confirmation)")
                phase = "STOP_HUNT"
        
        # Score: Delta divergence (max +2)
        if divergence != "none":
            score += 2
            reasons.append(f"{divergence.capitalize()} delta divergence")
        
        # Score: Volume spike (max +1)
        if vol_spike.get("detected"):
            ratio = vol_spike.get("ratio", 0)
            if ratio >= 5:
                score += 1
                reasons.append(f"Extreme volume spike ({ratio}x)")
            elif ratio >= 3:
                score += 1
                reasons.append(f"Volume spike ({ratio}x)")
        
        # Determine direction
        signal_direction = "FLAT"
        entry_price = 0
        stop_loss = 0
        targets = {}
        
        if phase == "ENTRY_CONFIRMED":
            # Check stop hunt direction
            if stop_hunt.get("direction") == "long_stop_hunt":
                signal_direction = "LONG"
                entry_price = self.current_price
                stop_loss = stop_hunt.get("swept_level", 0) * 0.998
                tp1 = entry_price + (entry_price - stop_loss) * 1.5
                tp2 = entry_price + (entry_price - stop_loss) * 3.0
                targets = {"tp1": round(tp1, 2), "tp2": round(tp2, 2)}
            elif stop_hunt.get("direction") == "short_stop_hunt":
                signal_direction = "SHORT"
                entry_price = self.current_price
                stop_loss = stop_hunt.get("swept_level", 0) * 1.002
                tp1 = entry_price - (stop_loss - entry_price) * 1.5
                tp2 = entry_price - (stop_loss - entry_price) * 3.0
                targets = {"tp1": round(tp1, 2), "tp2": round(tp2, 2)}
        
        # Check for conflicting signals
        if absorption.get("detected") and iceberg.get("detected"):
            if absorption.get("side") != iceberg.get("side"):
                conflicts.append("Absorption and iceberg on opposite sides")
                score -= 2
        
        if stop_hunt.get("detected") and not stop_hunt.get("confirmed"):
            warnings.append("Stop hunt not fully confirmed - wait for delta flip")
        
        # Determine conviction level
        if score >= HIGH_CONVICTION_SCORE:
            conviction = "HIGH"
        elif score >= MEDIUM_CONVICTION_SCORE:
            conviction = "MEDIUM"
        else:
            conviction = "LOW"
        
        # Only generate signal if score meets minimum threshold
        if score < MIN_CONVICTION_SCORE:
            signal_direction = "MONITOR"
            conviction = "LOW"
        
        # Calculate risk-reward ratio
        rr_ratio = 0
        if signal_direction in ["LONG", "SHORT"] and entry_price > 0 and stop_loss > 0:
            risk = abs(entry_price - stop_loss)
            reward = abs(targets.get("tp2", 0) - entry_price)
            rr_ratio = round(reward / risk, 2) if risk > 0 else 0
        
        # Build primary reason
        primary_reason = "; ".join(reasons[:3]) if reasons else "No strong signals detected"
        
        # Build institutional narrative
        narrative_parts = []
        if stop_hunt.get("detected"):
            narrative_parts.append(f"Stop hunt {'confirmed' if stop_hunt.get('confirmed') else 'detected'}")
        if absorption.get("detected"):
            narrative_parts.append(f"{absorption.get('side', 'unknown')} absorption active")
        if iceberg.get("detected"):
            narrative_parts.append("Institutional iceberg order present")
        if divergence != "none":
            narrative_parts.append(f"{divergence} delta divergence")
        
        institutional_narrative = ". ".join(narrative_parts) if narrative_parts else "Monitoring for institutional activity"
        
        # Build invalidation condition
        invalidation = ""
        if signal_direction == "LONG":
            invalidation = f"Price closes below {stop_loss:.2f}"
        elif signal_direction == "SHORT":
            invalidation = f"Price closes above {stop_loss:.2f}"
        
        signal = {
            "signal": signal_direction,
            "conviction": conviction,
            "total_score": score,
            "phase": phase,
            "primary_reason": primary_reason,
            "institutional_narrative": institutional_narrative,
            "invalidation": invalidation,
            "entry": {"price": round(entry_price, 2)},
            "stop_loss": {"price": round(stop_loss, 2)},
            "targets": targets,
            "rr_ratio": rr_ratio,
            "fingerprints_detected": {
                "absorption": {
                    "detected": absorption.get("detected", False),
                    "score": 3 if absorption.get("duration_candles", 0) >= 3 else 2 if absorption.get("duration_candles", 0) >= 2 else 1 if absorption.get("detected") else 0,
                    "detail": f"{absorption.get('side', 'none')} | {absorption.get('duration_candles', 0)} candles" if absorption.get("detected") else ""
                },
                "iceberg": {
                    "detected": iceberg.get("detected", False),
                    "score": 2 if iceberg.get("refresh_count", 0) >= 8 else 1 if iceberg.get("detected") else 0,
                    "detail": f"{iceberg.get('refresh_count', 0)} refreshes | est. {iceberg.get('estimated_true_size', 0):.2f}" if iceberg.get("detected") else ""
                },
                "stop_hunt": {
                    "detected": stop_hunt.get("detected", False),
                    "score": 4 if stop_hunt.get("confirmed") else 3 if stop_hunt.get("price_reclaimed") else 2 if stop_hunt.get("detected") else 0,
                    "detail": f"{stop_hunt.get('direction', 'none')} | Swept {stop_hunt.get('swept_level', 0):.2f}" if stop_hunt.get("detected") else ""
                },
                "delta_divergence": {
                    "detected": divergence != "none",
                    "score": 2 if divergence != "none" else 0,
                    "detail": divergence if divergence != "none" else ""
                },
                "volume_spike": {
                    "detected": vol_spike.get("detected", False),
                    "score": 1 if vol_spike.get("detected") else 0,
                    "detail": f"{vol_spike.get('ratio', 0):.1f}x volume" if vol_spike.get("detected") else ""
                }
            },
            "conflicts": conflicts,
            "warnings": warnings,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        return signal

    # ─────────────────────────────────────────
    # LLM SIGNAL GENERATION (DEPRECATED - Kept for reference)
    # ─────────────────────────────────────────

    async def get_signal_old(self, payload: dict) -> dict:
        system_prompt = open("institutional_entry_prompt.txt").read()

        async with aiohttp.ClientSession() as session:
            response = await session.post(
                ANTHROPIC_API_URL,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": 2000,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": json.dumps(payload, indent=2)}]
                }
            )
            data = await response.json()

        text = data["content"][0]["text"]
        # Strip markdown fences if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())

    # ─────────────────────────────────────────
    # WEBSOCKET STREAMS
    # ─────────────────────────────────────────

    async def run(self):
        streams = f"{self.symbol}@depth@100ms/{self.symbol}@trade"
        url = f"{BINANCE_WS_BASE}/{streams}"

        print(f"[ENGINE] Connecting to Binance: {url}")

        signal_interval = 300  # Generate signal every 5 min candle
        last_signal_time = 0

        async with websockets.connect(url) as ws:
            async for raw in ws:
                data = json.loads(raw)
                stream = data.get("stream", "")

                if "depth" in stream:
                    self.process_depth_update(data["data"])
                elif "trade" in stream:
                    self.process_trade(data["data"])

                if self.on_market_update:
                    await self.on_market_update(self.build_market_state())

                now = time.time()
                if now - last_signal_time >= signal_interval and self.current_price > 0:
                    try:
                        # Generate signal using rule-based logic (NO LLM)
                        signal = self.generate_signal()
                        signal["payload"] = self.build_payload()
                        self.latest_signal = signal
                        self.signal_history.appendleft(signal)
                        if self.on_signal:
                            await self.on_signal(signal)
                        
                        # Send Telegram notification for significant signals
                        if signal.get("signal") in ["LONG", "SHORT"] and signal.get("conviction") in ["HIGH", "MEDIUM"]:
                            await self.telegram.send_signal(signal)
                        
                        print(f"[SIGNAL] {signal.get('signal')} | {signal.get('conviction')} | Score: {signal.get('total_score')}")
                    except Exception as e:
                        print(f"[ERROR] Signal generation failed: {e}")
                        import traceback
                        traceback.print_exc()
                    last_signal_time = now

    def build_market_state(self) -> dict:
        """Lightweight state for UI real-time updates"""
        c = self.current_candle
        absorption = self.detect_absorption()
        iceberg = self.detect_iceberg()
        stop_hunt = self.detect_stop_hunt()

        top_bids = sorted(self.bids.items(), reverse=True)[:10]
        top_asks = sorted(self.asks.items())[:10]

        return {
            "price": self.current_price,
            "delta": round(c.delta if c else 0, 2),
            "cumulative_delta": round(self.cumulative_delta, 2),
            "absorption": absorption,
            "iceberg": iceberg,
            "stop_hunt": stop_hunt,
            "divergence": self.detect_delta_divergence(),
            "spoofs_60s": len([s for s in self.spoof_log if time.time() * 1000 - s["time"] < 60000]),
            "top_bids": [{"price": p, "qty": q} for p, q in top_bids],
            "top_asks": [{"price": p, "qty": q} for p, q in top_asks],
            "phase": {
                "absorption_active": absorption["detected"],
                "stop_hunt_occurred": self.phase.stop_hunt_occurred,
                "delta_confirmed": self.phase.delta_confirmed,
                "reclaim_confirmed": self.phase.reclaim_confirmed
            },
            "latest_signal": self.latest_signal,
            "timestamp": time.time()
        }


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    engine = InstitutionalEntryEngine(SYMBOL)
    asyncio.run(engine.run())
