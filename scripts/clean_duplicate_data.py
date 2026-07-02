"""
Clean duplicate and invalid data from PostgreSQL
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def get_connection():
    return psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        database=Config.POSTGRES_DB
    )

def clean_ods_daily_metrics():
    """Remove duplicate records from ods_daily_metrics"""
    print("Cleaning ods_daily_metrics...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count duplicates before cleaning
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT coin_id, DATE(fetched_at) as date, COUNT(*) as cnt
            FROM ods_daily_metrics
            GROUP BY coin_id, DATE(fetched_at)
            HAVING COUNT(*) > 1
        ) t
    """)
    dup_count = cursor.fetchone()[0]
    print(f"Found {dup_count} duplicate groups in ods_daily_metrics")
    
    # Delete duplicates, keep the latest record per coin per day
    cursor.execute("""
        DELETE FROM ods_daily_metrics
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY coin_id, DATE(fetched_at)
                           ORDER BY fetched_at DESC
                       ) as rn
                FROM ods_daily_metrics
            ) t
            WHERE rn > 1
        )
    """)
    
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Deleted {deleted} duplicate records from ods_daily_metrics")
    return deleted

def clean_real_time_prices():
    """Remove exact duplicate records from real_time_prices"""
    print("\nCleaning real_time_prices...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Count total records
    cursor.execute("SELECT COUNT(*) FROM real_time_prices")
    total = cursor.fetchone()[0]
    print(f"Total records: {total:,}")
    
    # Count exact duplicates (same symbol, price, timestamp)
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT symbol, current_price, processed_at, COUNT(*) as cnt
            FROM real_time_prices
            GROUP BY symbol, current_price, processed_at
            HAVING COUNT(*) > 1
        ) t
    """)
    dup_groups = cursor.fetchone()[0]
    print(f"Found {dup_groups} exact duplicate groups")
    
    # Delete exact duplicates, keep one
    cursor.execute("""
        DELETE FROM real_time_prices
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY symbol, current_price, processed_at
                           ORDER BY id
                       ) as rn
                FROM real_time_prices
            ) t
            WHERE rn > 1
        )
    """)
    
    deleted = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"Deleted {deleted} duplicate records from real_time_prices")
    return deleted

def clean_invalid_data():
    """Remove records with invalid prices (NULL or <= 0)"""
    print("\nCleaning invalid data...")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Clean ods_daily_metrics
    cursor.execute("""
        DELETE FROM ods_daily_metrics
        WHERE current_price IS NULL 
           OR current_price <= 0
           OR total_volume IS NULL
    """)
    deleted_ods = cursor.rowcount
    conn.commit()
    
    # Clean real_time_prices
    cursor.execute("""
        DELETE FROM real_time_prices
        WHERE current_price IS NULL 
           OR current_price <= 0
    """)
    deleted_rt = cursor.rowcount
    conn.commit()
    
    cursor.close()
    conn.close()
    
    print(f"Deleted {deleted_ods} invalid records from ods_daily_metrics")
    print(f"Deleted {deleted_rt} invalid records from real_time_prices")
    
    return deleted_ods, deleted_rt

def show_stats():
    """Show data statistics after cleaning"""
    print("\n" + "="*60)
    print("DATA STATISTICS AFTER CLEANING")
    print("="*60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # ods_daily_metrics stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT coin_id) as unique_coins,
            MIN(fetched_at) as earliest,
            MAX(fetched_at) as latest
        FROM ods_daily_metrics
    """)
    ods_stats = cursor.fetchone()
    print(f"\nods_daily_metrics:")
    print(f"  Total records: {ods_stats[0]:,}")
    print(f"  Unique coins: {ods_stats[1]}")
    print(f"  Date range: {ods_stats[2]} to {ods_stats[3]}")
    
    # real_time_prices stats
    cursor.execute("""
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT symbol) as unique_symbols,
            MIN(processed_at) as earliest,
            MAX(processed_at) as latest
        FROM real_time_prices
    """)
    rt_stats = cursor.fetchone()
    print(f"\nreal_time_prices:")
    print(f"  Total records: {rt_stats[0]:,}")
    print(f"  Unique symbols: {rt_stats[1]}")
    print(f"  Date range: {rt_stats[2]} to {rt_stats[3]}")
    
    cursor.close()
    conn.close()
    
    print("="*60)

if __name__ == "__main__":
    print("="*60)
    print("DATA CLEANING SCRIPT")
    print("="*60)
    
    # Clean duplicates
    clean_ods_daily_metrics()
    clean_real_time_prices()
    
    # Clean invalid data
    clean_invalid_data()
    
    # Show final stats
    show_stats()
    
    print("\n Data cleaning complete!")