import requests
import json
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class DiscordNotifier:
    def __init__(self):
        self.webhook_url = Config.DISCORD_WEBHOOK_URL
    
    def send_alert(self, alerts):
        if not alerts:
            logger.info("No alerts to send")
            return False
        
        fields = []
        for alert in alerts:
            symbol = alert['symbol']
            current = alert['current_price']
            change = alert['change_percent']
            
            # Discord color: 3066993 (Green) if positive, 15158332 (Red) if negative
            color = 3066993 if change > 0 else 15158332
            
            fields.append({
                "name": symbol,
                "value": f"Current: ${current:,.2f}\nChange: {change:+.2f}%",
                "inline": True
            })

        payload = {
            "content": "ALERT: Significant crypto price changes detected (>5%)",
            "embeds": [
                {
                    "title": "Crypto Price Alert",
                    "color": color,
                    "fields": fields,
                    "footer": {
                        "text": f"Generated at {alerts[0]['timestamp']}"
                    }
                }
            ]
        }
        
        return self._send_payload(payload)

    def send_daily_summary(self, top_movers):
        if not top_movers:
            return False
        
        fields = []
        for i, mover in enumerate(top_movers, 1):
            color = 3066993 if mover['change_percent'] > 0 else 15158332
            fields.append({
                "name": f"{i}. {mover['symbol']}",
                "value": f"Change: {mover['change_percent']:+.2f}%\nPrice: ${mover['current_price']:,.2f}",
                "inline": True
            })

        payload = {
            "content": "Daily Summary: Top crypto movers in the last 24 hours",
            "embeds": [
                {
                    "title": "Daily Crypto Summary",
                    "color": 3447003,
                    "fields": fields
                }
            ]
        }
        
        return self._send_payload(payload)

    def _send_payload(self, payload):
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 204]:
                logger.info("Successfully sent notification to Discord")
                return True
            else:
                logger.error(f"Discord API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Discord notification: {e}")
            return False