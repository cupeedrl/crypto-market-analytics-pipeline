import psycopg2
from datetime import datetime, timedelta
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PriceMonitor:
    def __init__(self):
        self.conn_params = {
            'host': Config.POSTGRES_HOST,
            'port': Config.POSTGRES_PORT,
            'database': Config.POSTGRES_DB,
            'user': Config.POSTGRES_USER,
            'password': Config.POSTGRES_PASSWORD
        }
        self.threshold = 0.5  # 0.1% change threshold
    
    def get_connection(self):
        """Connect to PostgreSQL"""
        return psycopg2.connect(**self.conn_params)
    
    def check_price_changes(self, hours=1):
        """
        Check price changes in last N hours
        
        Returns: List of alerts with symbol, current_price, previous_price, change_percent
        FIX: Dùng DISTINCT ON để lấy 1 record mới nhất per symbol
        """
        alerts = []
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # FIX: DISTINCT ON để lấy 1 record mới nhất per symbol
                query = """
                WITH current_prices AS (
                    SELECT DISTINCT ON (symbol)
                        symbol,
                        current_price,
                        processed_at
                    FROM real_time_prices
                    WHERE processed_at >= NOW() - INTERVAL '5 minutes'
                    ORDER BY symbol, processed_at DESC
                ),
                previous_prices AS (
                    SELECT 
                        symbol,
                        AVG(current_price) as avg_price
                    FROM real_time_prices
                    WHERE processed_at >= NOW() - INTERVAL '%s hours'
                      AND processed_at < NOW() - INTERVAL '5 minutes'
                    GROUP BY symbol
                ),
                price_changes AS (
                    SELECT 
                        c.symbol,
                        c.current_price,
                        p.avg_price as previous_price,
                        ((c.current_price - p.avg_price) / p.avg_price * 100) as change_percent
                    FROM current_prices c
                    JOIN previous_prices p ON c.symbol = p.symbol
                )
                SELECT 
                    symbol,
                    current_price,
                    previous_price,
                    change_percent
                FROM price_changes
                WHERE ABS(change_percent) > %s
                ORDER BY ABS(change_percent) DESC
                LIMIT 20;
                """
                
                cursor.execute(query, (hours, self.threshold))
                results = cursor.fetchall()
                
                for row in results:
                    symbol, current_price, previous_price, change_percent = row
                    alerts.append({
                        'symbol': symbol,
                        'current_price': float(current_price),
                        'previous_price': float(previous_price),
                        'change_percent': float(change_percent),
                        'timestamp': datetime.now().isoformat()
                    })
                
                cursor.close()
                
                if alerts:
                    logger.info(f"Found {len(alerts)} price alerts")
                else:
                    logger.info("No significant price changes detected")
                
                return alerts
                
        except Exception as e:
            logger.error(f"Error checking price changes: {e}")
            return []
    
    def get_top_movers(self, limit=5):
        """Get top N price movers in last hour"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # FIX: DISTINCT ON để lấy 1 record mới nhất và 1 cũ nhất per symbol
                query = """
                WITH latest AS (
                    SELECT DISTINCT ON (symbol)
                        symbol,
                        current_price as latest_price
                    FROM real_time_prices
                    WHERE processed_at >= NOW() - INTERVAL '1 hour'
                    ORDER BY symbol, processed_at DESC
                ),
                oldest AS (
                    SELECT DISTINCT ON (symbol)
                        symbol,
                        current_price as oldest_price
                    FROM real_time_prices
                    WHERE processed_at >= NOW() - INTERVAL '1 hour'
                    ORDER BY symbol, processed_at ASC
                )
                SELECT 
                    l.symbol,
                    l.latest_price as current_price,
                    o.oldest_price,
                    ((l.latest_price - o.oldest_price) / o.oldest_price * 100) as change_percent
                FROM latest l
                JOIN oldest o ON l.symbol = o.symbol
                WHERE o.oldest_price > 0
                ORDER BY ABS(((l.latest_price - o.oldest_price) / o.oldest_price * 100)) DESC
                LIMIT %s;
                """
                
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                cursor.close()
                
                return [
                    {
                        'symbol': row[0],
                        'current_price': float(row[1]),
                        'oldest_price': float(row[2]),
                        'change_percent': float(row[3])
                    }
                    for row in results
                ]
                
        except Exception as e:
            logger.error(f"Error getting top movers: {e}")
            return []