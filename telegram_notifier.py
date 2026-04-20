"""
Telegram Notification System
Sends trading signals and alerts via Telegram Bot API
"""

import aiohttp
import os
from typing import Optional


class TelegramNotifier:
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}" if self.bot_token else None
        
    async def send_signal(self, signal_data: dict):
        """Send trading signal notification"""
        if not self.is_configured():
            print("[TELEGRAM] Not configured - skipping notification")
            return False
            
        signal = signal_data.get("signal", "UNKNOWN")
        conviction = signal_data.get("conviction", "LOW")
        score = signal_data.get("total_score", 0)
        
        # Format message
        emoji = {
            "LONG": "🟢",
            "SHORT": "🔴",
            "MONITOR": "🟡",
            "FLAT": "⚪"
        }.get(signal, "⚪")
        
        conviction_emoji = {
            "HIGH": "🔥",
            "MEDIUM": "⚡",
            "LOW": "💤"
        }.get(conviction, "")
        
        message = f"""
{emoji} *INSTITUTIONAL SIGNAL* {conviction_emoji}

*Signal:* {signal}
*Conviction:* {conviction}
*Score:* {score:+d}

*Entry:* ${signal_data.get('entry', {}).get('price', 0):,.2f}
*Stop Loss:* ${signal_data.get('stop_loss', {}).get('price', 0):,.2f}
*Target:* ${signal_data.get('targets', {}).get('tp2', 0):,.2f}
*R:R Ratio:* 1:{signal_data.get('rr_ratio', 0):.1f}

*Phase:* {signal_data.get('phase', 'N/A')}
*Reason:* {signal_data.get('primary_reason', 'N/A')[:150]}

_Time: {signal_data.get('timestamp', 'N/A')}_
        """.strip()
        
        return await self._send_message(message, parse_mode="Markdown")
    
    async def send_alert(self, title: str, message: str, level: str = "INFO"):
        """Send general alert notification"""
        if not self.is_configured():
            return False
            
        emoji = {
            "INFO": "ℹ️",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "SUCCESS": "✅"
        }.get(level, "ℹ️")
        
        formatted_message = f"{emoji} *{title}*\n\n{message}"
        return await self._send_message(formatted_message, parse_mode="Markdown")
    
    async def send_market_update(self, state: dict):
        """Send periodic market status update"""
        if not self.is_configured():
            return False
            
        price = state.get("price", 0)
        delta = state.get("delta", 0)
        absorption = state.get("absorption", {})
        stop_hunt = state.get("stop_hunt", {})
        
        message = f"""
📊 *MARKET UPDATE*

*Price:* ${price:,.2f}
*Delta:* {delta:+.2f}

*Absorption:* {'✅ Active' if absorption.get('detected') else '❌ Inactive'}
*Stop Hunt:* {'✅ Detected' if stop_hunt.get('detected') else '❌ None'}
*Spoofs (60s):* {state.get('spoofs_60s', 0)}
        """.strip()
        
        return await self._send_message(message, parse_mode="Markdown")
    
    async def _send_message(self, text: str, parse_mode: str = "HTML"):
        """Send message to Telegram"""
        if not self.base_url or not self.chat_id:
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/sendMessage"
                payload = {
                    "chat_id": self.chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True
                }
                
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    if result.get("ok"):
                        print(f"[TELEGRAM] Message sent successfully")
                        return True
                    else:
                        print(f"[TELEGRAM] Error: {result.get('description')}")
                        return False
        except Exception as e:
            print(f"[TELEGRAM] Failed to send message: {e}")
            return False
    
    def is_configured(self) -> bool:
        """Check if Telegram is properly configured"""
        return bool(self.bot_token and self.chat_id)
