"""
XAUUSD Smart Money Concepts (SMC) Monitor
Implements: BOS/CHOCH + HTF Bias + FVG + Liquidity Zones
Uses Twelve Data API for market data
"""

import asyncio
import aiohttp
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/xauusd_smc.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('XAUUSD_SMC')


class TrendBias(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"


class StructureType(Enum):
    BOS = "BOS"
    CHOCH = "CHOCH"


@dataclass
class SwingPoint:
    index: int
    price: float
    timestamp: datetime
    is_high: bool


@dataclass
class FairValueGap:
    top: float
    bottom: float
    midpoint: float
    created_at: datetime
    is_bullish: bool
    mitigated: bool = False
    mitigation_time: Optional[datetime] = None


@dataclass
class LiquidityZone:
    price: float
    zone_type: str
    created_at: datetime
    breached: bool = False
    breach_time: Optional[datetime] = None
    strength: int = 0


@dataclass
class SMCSignal:
    signal_type: str
    direction: str
    price: float
    timestamp: datetime
    confidence: float
    description: str
    htf_bias: TrendBias
    fvg_present: bool = False
    liquidity_zone_nearby: bool = False


class TwelveDataClient:
    """Client for Twelve Data API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.twelvedata.com"
        self.session = None
        
    async def init_session(self):
        self.session = aiohttp.ClientSession()
        
    async def close_session(self):
        if self.session:
            await self.session.close()
            
    async def get_candles(self, symbol: str, interval: str, outputsize: int = 500) -> List[Dict]:
        """Get OHLCV candles"""
        url = f"{self.base_url}/time_series"
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': self.api_key
        }
        
        try:
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                if 'values' in data:
                    return data['values']
                else:
                    logger.error(f"API Error: {data}")
                    return []
        except Exception as e:
            logger.error(f"Error fetching candles: {e}")
            return []
            
    async def get_htf_candles(self, symbol: str, interval: str, outputsize: int = 100) -> List[Dict]:
        """Get higher timeframe candles for bias analysis"""
        return await self.get_candles(symbol, interval, outputsize)


class SmartMoneyAnalyzer:
    """Core SMC Analysis Engine"""
    
    def __init__(self, swing_length: int = 10, detection_length: int = 7):
        self.swing_length = swing_length
        self.detection_length = detection_length
        self.swings: List[SwingPoint] = []
        self.fvgs: List[FairValueGap] = []
        self.liquidity_zones: List[LiquidityZone] = []
        self.current_bias = TrendBias.NEUTRAL
        self.last_structure_high: Optional[float] = None
        self.last_structure_low: Optional[float] = None
        self.signals: List[SMCSignal] = []
        
    def detect_swings(self, candles: List[Dict]) -> List[SwingPoint]:
        """Detect pivot highs and lows"""
        swings = []
        n = len(candles)
        
        for i in range(self.swing_length, n - self.swing_length - 1):
            is_high = True
            current_high = float(candles[i]['high'])
            for j in range(1, self.swing_length + 1):
                if float(candles[i-j]['high']) >= current_high or float(candles[i+j]['high']) >= current_high:
                    is_high = False
                    break
                    
            if is_high:
                swings.append(SwingPoint(
                    index=i,
                    price=current_high,
                    timestamp=datetime.strptime(candles[i]['datetime'], '%Y-%m-%d %H:%M:%S'),
                    is_high=True
                ))
                
            is_low = True
            current_low = float(candles[i]['low'])
            for j in range(1, self.swing_length + 1):
                if float(candles[i-j]['low']) <= current_low or float(candles[i+j]['low']) <= current_low:
                    is_low = False
                    break
                    
            if is_low:
                swings.append(SwingPoint(
                    index=i,
                    price=current_low,
                    timestamp=datetime.strptime(candles[i]['datetime'], '%Y-%m-%d %H:%M:%S'),
                    is_high=False
                ))
                
        return sorted(swings, key=lambda x: x.index)
        
    def detect_bos_choch(self, swings: List[SwingPoint], current_price: float) -> List[Tuple[StructureType, str]]:
        """Detect Break of Structure and Change of Character"""
        structures = []
        
        if len(swings) < 4:
            return structures
            
        recent_swings = swings[-6:]
        
        if len(recent_swings) >= 2:
            last_high = max([s.price for s in recent_swings if s.is_high], default=0)
            last_low = min([s.price for s in recent_swings if not s.is_high], default=float('inf'))
            
            if current_price > last_high and last_high > 0:
                if self.current_bias == TrendBias.BEARISH:
                    structures.append((StructureType.CHOCH, "bullish"))
                    self.current_bias = TrendBias.BULLISH
                elif self.current_bias == TrendBias.BULLISH or self.current_bias == TrendBias.NEUTRAL:
                    structures.append((StructureType.BOS, "bullish"))
                    self.current_bias = TrendBias.BULLISH
                    
            elif current_price < last_low and last_low < float('inf'):
                if self.current_bias == TrendBias.BULLISH:
                    structures.append((StructureType.CHOCH, "bearish"))
                    self.current_bias = TrendBias.BEARISH
                elif self.current_bias == TrendBias.BEARISH or self.current_bias == TrendBias.NEUTRAL:
                    structures.append((StructureType.BOS, "bearish"))
                    self.current_bias = TrendBias.BEARISH
                    
        return structures
        
    def detect_fvg(self, candles: List[Dict]) -> List[FairValueGap]:
        """Detect Fair Value Gaps"""
        fvgs = []
        n = len(candles)
        
        for i in range(2, n):
            curr = candles[i]
            prev2 = candles[i-2]
            
            curr_open = float(curr['open'])
            curr_close = float(curr['close'])
            curr_high = float(curr['high'])
            curr_low = float(curr['low'])
            
            prev2_open = float(prev2['open'])
            prev2_close = float(prev2['close'])
            prev2_high = float(prev2['high'])
            prev2_low = float(prev2['low'])
            
            if curr_low > prev2_high:
                gap_top = curr_low
                gap_bottom = prev2_high
                gap_mid = (gap_top + gap_bottom) / 2
                
                fvgs.append(FairValueGap(
                    top=gap_top,
                    bottom=gap_bottom,
                    midpoint=gap_mid,
                    created_at=datetime.strptime(curr['datetime'], '%Y-%m-%d %H:%M:%S'),
                    is_bullish=True
                ))
                
            elif curr_high < prev2_low:
                gap_top = prev2_low
                gap_bottom = curr_high
                gap_mid = (gap_top + gap_bottom) / 2
                
                fvgs.append(FairValueGap(
                    top=gap_top,
                    bottom=gap_bottom,
                    midpoint=gap_mid,
                    created_at=datetime.strptime(curr['datetime'], '%Y-%m-%d %H:%M:%S'),
                    is_bullish=False
                ))
                
        return fvgs[-10:]
        
    def check_fvg_mitigation(self, fvgs: List[FairValueGap], current_price: float) -> List[FairValueGap]:
        """Check if FVGs have been mitigated"""
        for fvg in fvgs:
            if not fvg.mitigated:
                if fvg.is_bullish and current_price <= fvg.bottom:
                    fvg.mitigated = True
                    fvg.mitigation_time = datetime.now()
                elif not fvg.is_bullish and current_price >= fvg.top:
                    fvg.mitigated = True
                    fvg.mitigation_time = datetime.now()
        return fvgs
        
    def detect_liquidity_zones(self, swings: List[SwingPoint], atr: float) -> List[LiquidityZone]:
        """Detect buyside and sellside liquidity zones"""
        zones = []
        margin = atr / 6.9
        
        for swing in swings[-20:]:
            if swing.is_high:
                zones.append(LiquidityZone(
                    price=swing.price + margin,
                    zone_type="buyside",
                    created_at=swing.timestamp,
                    strength=1
                ))
            else:
                zones.append(LiquidityZone(
                    price=swing.price - margin,
                    zone_type="sellside",
                    created_at=swing.timestamp,
                    strength=1
                ))
                
        merged_zones = []
        for zone in zones:
            merged = False
            for mz in merged_zones:
                if abs(mz.price - zone.price) < atr * 0.5 and mz.zone_type == zone.zone_type:
                    mz.strength += 1
                    merged = True
                    break
            if not merged:
                merged_zones.append(zone)
                
        return merged_zones[-10:]
        
    def analyze_htf_bias(self, htf_candles: List[Dict]) -> TrendBias:
        """Analyze higher timeframe bias using EMA crossover"""
        if len(htf_candles) < 50:
            return TrendBias.NEUTRAL
            
        closes = [float(c['close']) for c in htf_candles]
        
        ema_fast = self._calculate_ema(closes, 20)
        ema_slow = self._calculate_ema(closes, 50)
        
        if ema_fast[-1] > ema_slow[-1]:
            return TrendBias.BULLISH
        elif ema_fast[-1] < ema_slow[-1]:
            return TrendBias.BEARISH
        else:
            return TrendBias.NEUTRAL
            
    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """Calculate Exponential Moving Average"""
        multiplier = 2 / (period + 1)
        ema = [prices[0]]
        
        for i in range(1, len(prices)):
            ema_value = (prices[i] * multiplier) + (ema[-1] * (1 - multiplier))
            ema.append(ema_value)
            
        return ema
        
    def calculate_atr(self, candles: List[Dict], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(candles) < period + 1:
            return 0
            
        true_ranges = []
        for i in range(1, len(candles)):
            high = float(candles[i]['high'])
            low = float(candles[i]['low'])
            prev_close = float(candles[i-1]['close'])
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            true_ranges.append(tr)
            
        return sum(true_ranges[-period:]) / period
        
    def generate_signals(self, candles: List[Dict], current_price: float, 
                        structures: List[Tuple[StructureType, str]],
                        fvgs: List[FairValueGap],
                        liquidity_zones: List[LiquidityZone],
                        htf_bias: TrendBias) -> List[SMCSignal]:
        """Generate trading signals based on SMC confluence"""
        signals = []
        
        if not structures:
            return signals
            
        for struct_type, direction in structures:
            confidence = 0.5
            
            fvg_nearby = False
            for fvg in fvgs:
                if not fvg.mitigated:
                    if direction == "bullish" and fvg.is_bullish:
                        if abs(current_price - fvg.midpoint) < (fvg.top - fvg.bottom) * 2:
                            fvg_nearby = True
                            confidence += 0.15
                    elif direction == "bearish" and not fvg.is_bullish:
                        if abs(current_price - fvg.midpoint) < (fvg.top - fvg.bottom) * 2:
                            fvg_nearby = True
                            confidence += 0.15
                            
            liq_nearby = False
            for zone in liquidity_zones:
                if not zone.breached:
                    if direction == "bullish" and zone.zone_type == "sellside":
                        if abs(current_price - zone.price) < 5:
                            liq_nearby = True
                            confidence += 0.15
                    elif direction == "bearish" and zone.zone_type == "buyside":
                        if abs(current_price - zone.price) < 5:
                            liq_nearby = True
                            confidence += 0.15
                            
            if (direction == "bullish" and htf_bias == TrendBias.BULLISH) or \
               (direction == "bearish" and htf_bias == TrendBias.BEARISH):
                confidence += 0.2
                
            if confidence >= 0.6:
                signal = SMCSignal(
                    signal_type=struct_type.value,
                    direction=direction,
                    price=current_price,
                    timestamp=datetime.now(),
                    confidence=confidence,
                    description=f"{struct_type.value} {direction.upper()} | HTF: {htf_bias.value} | FVG: {'Yes' if fvg_nearby else 'No'} | Liq: {'Yes' if liq_nearby else 'No'}",
                    htf_bias=htf_bias,
                    fvg_present=fvg_nearby,
                    liquidity_zone_nearby=liq_nearby
                )
                signals.append(signal)
                
        return signals


class XAUUSDSMCMonitor:
    """Main monitoring system for XAUUSD"""
    
    def __init__(self):
        self.api_key = os.getenv('TWELVE_DATA_API_KEY')
        if not self.api_key:
            raise ValueError("TWELVE_DATA_API_KEY not found in environment variables")
            
        self.symbol = "XAUUSD"
        self.interval = "5min"
        self.htf_interval = "4h"
        
        self.client = TwelveDataClient(self.api_key)
        self.analyzer = SmartMoneyAnalyzer(swing_length=10, detection_length=7)
        
        self.running = False
        self.monitoring_interval = 300
        
    async def start(self):
        """Start the monitoring system"""
        await self.client.init_session()
        self.running = True
        
        logger.info("="*60)
        logger.info("XAUUSD Smart Money Concepts Monitor Started")
        logger.info("="*60)
        logger.info(f"Symbol: {self.symbol}")
        logger.info(f"Timeframe: {self.interval}")
        logger.info(f"HTF Timeframe: {self.htf_interval}")
        logger.info(f"Monitoring Interval: {self.monitoring_interval}s")
        logger.info("="*60)
        
        while self.running:
            try:
                await self.run_analysis_cycle()
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
                await asyncio.sleep(60)
                
    async def stop(self):
        """Stop the monitoring system"""
        self.running = False
        await self.client.close_session()
        logger.info("Monitor stopped")
        
    async def run_analysis_cycle(self):
        """Run one complete analysis cycle"""
        logger.info("\n" + "="*60)
        logger.info(f"Analysis Cycle Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        
        candles = await self.client.get_candles(self.symbol, self.interval, outputsize=500)
        htf_candles = await self.client.get_htf_candles(self.symbol, self.htf_interval, outputsize=100)
        
        if not candles:
            logger.error("Failed to fetch candle data")
            return
            
        candles.reverse()
        htf_candles.reverse()
        
        current_price = float(candles[-1]['close'])
        logger.info(f"Current Price: ${current_price:.2f}")
        
        atr = self.analyzer.calculate_atr(candles, period=14)
        logger.info(f"ATR(14): ${atr:.2f}")
        
        swings = self.analyzer.detect_swings(candles)
        logger.info(f"Detected {len(swings)} swing points")
        
        htf_bias = self.analyzer.analyze_htf_bias(htf_candles)
        logger.info(f"HTF Bias: {htf_bias.value.upper()}")
        
        structures = self.analyzer.detect_bos_choch(swings, current_price)
        if structures:
            for struct_type, direction in structures:
                logger.info(f"🔔 {struct_type.value} detected: {direction.upper()}")
                
        fvgs = self.analyzer.detect_fvg(candles)
        fvgs = self.analyzer.check_fvg_mitigation(fvgs, current_price)
        active_fvgs = [f for f in fvgs if not f.mitigated]
        logger.info(f"Active FVGs: {len(active_fvgs)} (Bullish: {sum(1 for f in active_fvgs if f.is_bullish)}, Bearish: {sum(1 for f in active_fvgs if not f.is_bullish)})")
        
        liquidity_zones = self.analyzer.detect_liquidity_zones(swings, atr)
        unbreached_zones = [z for z in liquidity_zones if not z.breached]
        logger.info(f"Liquidity Zones: {len(unbreached_zones)} (Buyside: {sum(1 for z in unbreached_zones if z.zone_type == 'buyside')}, Sellside: {sum(1 for z in unbreached_zones if z.zone_type == 'sellside')})")
        
        signals = self.analyzer.generate_signals(
            candles, current_price, structures, fvgs, liquidity_zones, htf_bias
        )
        
        if signals:
            logger.info(f"\n🚨 SIGNALS GENERATED: {len(signals)}")
            for signal in signals:
                logger.info(f"   Type: {signal.signal_type}")
                logger.info(f"   Direction: {signal.direction.upper()}")
                logger.info(f"   Price: ${signal.price:.2f}")
                logger.info(f"   Confidence: {signal.confidence:.0%}")
                logger.info(f"   Details: {signal.description}")
                logger.info("-" * 40)
                
                await self.send_alert(signal)
        else:
            logger.info("No high-confidence signals generated")
            
        self.store_state({
            'timestamp': datetime.now().isoformat(),
            'current_price': current_price,
            'atr': atr,
            'htf_bias': htf_bias.value,
            'structures': [{'type': s[0].value, 'direction': s[1]} for s in structures],
            'active_fvgs': len(active_fvgs),
            'liquidity_zones': len(unbreached_zones),
            'signals': [{
                'type': sig.signal_type,
                'direction': sig.direction,
                'price': sig.price,
                'confidence': sig.confidence,
                'description': sig.description,
                'timestamp': sig.timestamp.isoformat()
            } for sig in signals]
        })
        
    async def send_alert(self, signal: SMCSignal):
        """Send alert via configured channels"""
        alert_data = {
            'symbol': self.symbol,
            'signal_type': signal.signal_type,
            'direction': signal.direction,
            'price': signal.price,
            'confidence': signal.confidence,
            'description': signal.description,
            'timestamp': signal.timestamp.isoformat(),
            'htf_bias': signal.htf_bias.value
        }
        
        logger.info(f"ALERT SENT: {json.dumps(alert_data, indent=2)}")
        
    def store_state(self, state: Dict):
        """Store current state for dashboard access"""
        state_file = 'xauusd_smc_state.json'
        try:
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error storing state: {e}")


async def main():
    """Entry point"""
    monitor = XAUUSDSMCMonitor()
    
    try:
        await monitor.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        await monitor.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        await monitor.stop()


if __name__ == "__main__":
    asyncio.run(main())
