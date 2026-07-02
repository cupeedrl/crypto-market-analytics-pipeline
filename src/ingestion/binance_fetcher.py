import requests
import pandas as pd
from datetime import datetime
from src.utils.logger import get_logger

logger = get_logger(__name__)

class BinanceFetcher:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        self.session = requests.Session()

    def fetch_top_coins(self, limit: int = 10) -> pd.DataFrame:
        """Lấy dữ liệu top coins từ Binance API"""
        url = f"{self.base_url}/ticker/24hr"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Filter USDT pairs và sort theo volume
            usdt_pairs = [item for item in data if item['symbol'].endswith('USDT')]
            top_coins = sorted(usdt_pairs, key=lambda x: float(x['quoteVolume']), reverse=True)[:limit]
            
            records = []
            for item in top_coins:
                symbol = item['symbol'].replace('USDT', '')
                records.append({
                    'coin_id': symbol.lower(),
                    'coin_name': symbol,
                    'symbol': symbol,
                    'current_price': float(item['lastPrice']),
                    'market_cap': 0,  # Binance không cung cấp market cap
                    'total_volume': float(item['quoteVolume']),
                    'price_change_24h': float(item['priceChange']),
                    'price_change_percent_24h': float(item['priceChangePercent']),
                    'fetched_at': datetime.utcnow()
                })
            
            logger.info(f"Successfully fetched {len(records)} coins from Binance.")
            return pd.DataFrame(records)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch data from Binance: {e}")
            return pd.DataFrame()