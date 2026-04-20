"""
Volume Profile Calculator
Tracks volume distribution across price levels for institutional analysis
"""

from collections import defaultdict


SESSION_CANDLES = 50  # Number of candles per session


class VolumeProfileCalculator:
    def __init__(self):
        self.price_volume: dict[float, float] = defaultdict(float)
        self.total_volume: float = 0.0
        self.high_price: float = 0.0
        self.low_price: float = float('inf')
        self.poc: float = 0.0  # Point of Control
        self.vah: float = 0.0  # Value Area High
        self.val: float = 0.0  # Value Area Low
        
    def add_trade(self, price: float, volume: float, timestamp: float):
        """Add a trade to the volume profile"""
        rounded_price = round(price, 2)
        self.price_volume[rounded_price] += volume
        self.total_volume += volume
        
        if price > self.high_price:
            self.high_price = price
        if price < self.low_price:
            self.low_price = price
            
        self._recalculate_poc()
        
    def _recalculate_poc(self):
        """Recalculate Point of Control (price with highest volume)"""
        if not self.price_volume:
            return
            
        self.poc = max(self.price_volume.keys(), key=lambda p: self.price_volume[p])
        self._calculate_value_area()
        
    def _calculate_value_area(self, percentage: float = 0.70):
        """Calculate Value Area (70% of total volume around POC)"""
        if not self.price_volume or self.total_volume == 0:
            return
            
        sorted_prices = sorted(self.price_volume.keys())
        target_volume = self.total_volume * percentage
        
        # Start from POC and expand outward
        poc_index = sorted_prices.index(self.poc) if self.poc in sorted_prices else len(sorted_prices) // 2
        
        left_idx = poc_index
        right_idx = poc_index
        accumulated_volume = self.price_volume.get(self.poc, 0)
        
        while accumulated_volume < target_volume:
            # Expand to the side with more volume
            left_vol = self.price_volume.get(sorted_prices[left_idx - 1], 0) if left_idx > 0 else 0
            right_vol = self.price_volume.get(sorted_prices[right_idx + 1], 0) if right_idx < len(sorted_prices) - 1 else 0
            
            if left_vol >= right_vol and left_idx > 0:
                left_idx -= 1
                accumulated_volume += left_vol
            elif right_idx < len(sorted_prices) - 1:
                right_idx += 1
                accumulated_volume += right_vol
            else:
                break
                
        self.val = sorted_prices[left_idx]
        self.vah = sorted_prices[right_idx]
        
    def new_session(self):
        """Start a new volume profile session"""
        self.price_volume.clear()
        self.total_volume = 0.0
        self.high_price = 0.0
        self.low_price = float('inf')
        self.poc = 0.0
        self.vah = 0.0
        self.val = 0.0
        
    def get_volume_at_price(self, price: float) -> float:
        """Get volume at a specific price level"""
        return self.price_volume.get(round(price, 2), 0.0)
    
    def is_above_poc(self, price: float) -> bool:
        """Check if price is above Point of Control"""
        return price > self.poc
    
    def is_below_poc(self, price: float) -> bool:
        """Check if price is below Point of Control"""
        return price < self.poc
    
    def is_in_value_area(self, price: float) -> bool:
        """Check if price is within Value Area"""
        return self.val <= price <= self.vah
    
    def to_payload(self, current_price: float) -> dict:
        """Generate payload for LLM analysis"""
        if self.total_volume == 0:
            return {
                "poc": 0,
                "vah": 0,
                "val": 0,
                "total_volume": 0,
                "current_vs_poc": "neutral",
                "current_in_va": False
            }
            
        # Determine position relative to POC
        if current_price > self.poc * 1.001:
            vs_poc = "above"
        elif current_price < self.poc * 0.999:
            vs_poc = "below"
        else:
            vs_poc = "at"
            
        return {
            "poc": round(self.poc, 2),
            "vah": round(self.vah, 2),
            "val": round(self.val, 2),
            "total_volume": round(self.total_volume, 4),
            "high": round(self.high_price, 2),
            "low": round(self.low_price, 2),
            "current_vs_poc": vs_poc,
            "current_in_va": self.is_in_value_area(current_price),
            "value_area_width_pct": round((self.vah - self.val) / self.poc * 100, 2) if self.poc > 0 else 0
        }
