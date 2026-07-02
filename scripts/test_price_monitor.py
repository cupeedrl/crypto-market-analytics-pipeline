import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.alerting.price_monitor import PriceMonitor
from datetime import datetime

def test_monitor():
    print("=" * 60)
    print("TESTING PRICE MONITOR")
    print("=" * 60)
    
    monitor = PriceMonitor()
    print(f"Threshold: {monitor.threshold}%")
    print()
    
    # Test check_price_changes
    print("[1] Checking price changes (last 1 hour)...")
    alerts = monitor.check_price_changes(hours=1)
    
    if alerts:
        print(f"Found {len(alerts)} alerts:")
        for alert in alerts[:10]:
            print(f"  - {alert['symbol']}: {alert['change_percent']:+.2f}% (${alert['current_price']:,.2f})")
    else:
        print("No alerts found")
        print("\n[DEBUG] Checking raw data...")
        
        # Query raw data
        import psycopg2
        from src.utils.config import Config
        
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DB
        )
        
        cursor = conn.cursor()
        
        # Check latest prices
        cursor.execute("""
            SELECT symbol, current_price, processed_at
            FROM real_time_prices
            WHERE processed_at >= NOW() - INTERVAL '5 minutes'
            ORDER BY processed_at DESC
            LIMIT 5
        """)
        latest = cursor.fetchall()
        print(f"\nLatest prices (last 5 min):")
        for row in latest:
            print(f"  {row[0]}: ${row[1]:,.2f} at {row[2]}")
        
        # Check historical average
        cursor.execute("""
            SELECT symbol, AVG(current_price) as avg_price, COUNT(*) as count
            FROM real_time_prices
            WHERE processed_at >= NOW() - INTERVAL '1 hour'
              AND processed_at < NOW() - INTERVAL '5 minutes'
            GROUP BY symbol
            LIMIT 5
        """)
        historical = cursor.fetchall()
        print(f"\nHistorical average (1h ago - 5min ago):")
        for row in historical:
            print(f"  {row[0]}: ${row[1]:,.2f} ({row[2]} records)")
        
        cursor.close()
        conn.close()
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    test_monitor()