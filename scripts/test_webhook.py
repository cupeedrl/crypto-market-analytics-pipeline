import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from src.utils.config import Config

def test_webhook():
    webhook_url = Config.DISCORD_WEBHOOK_URL
    
    print(f"Testing webhook: {webhook_url[:60]}...")
    
    # Test payload
    payload = {
        "content": "🚨 **TEST ALERT** - Crypto Price Alert System",
        "embeds": [{
            "title": "Webhook Test Successful",
            "description": "If you see this message, the webhook is working correctly!",
            "color": 3066993,  # Green
            "fields": [
                {
                    "name": "BTCUSDT",
                    "value": "Current: $60,000.00\nChange: +1.50%",
                    "inline": True
                },
                {
                    "name": "ETHUSDT",
                    "value": "Current: $3,000.00\nChange: -0.80%",
                    "inline": True
                }
            ],
            "footer": {
                "text": "Test message from Crypto Analytics Pipeline"
            }
        }]
    }
    
    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code in [200, 204]:
            print("SUCCESS! Check your Discord channel for the test message.")
            return True
        else:
            print(f"FAILED! Status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_webhook()
    sys.exit(0 if success else 1)