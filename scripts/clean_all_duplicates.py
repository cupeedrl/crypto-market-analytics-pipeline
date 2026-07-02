"""
Clean ALL duplicates - keep only 1 record per (symbol, processed_at)
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
        database=Config.POSTGRES_DB,
    )


def clean_all_duplicates():
    """Remove ALL duplicates, keep only 1 record per (symbol, processed_at)"""
    print("=" * 60)
    print("CLEANING ALL DUPLICATES")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    # Count before
    cursor.execute("SELECT COUNT(*) FROM real_time_prices")
    before_count = cursor.fetchone()[0]
    print(f"Total records before: {before_count:,}")

    # Count duplicate groups
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT symbol, processed_at
            FROM real_time_prices
            GROUP BY symbol, processed_at
            HAVING COUNT(*) > 1
        ) t
    """)
    dup_groups = cursor.fetchone()[0]
    print(f"Duplicate groups: {dup_groups:,}")

    # Delete all duplicates, keep the record with smallest id (first inserted)
    print("\nDeleting duplicates (keeping first record per timestamp)...")
    cursor.execute("""
        DELETE FROM real_time_prices
        WHERE id IN (
            SELECT id FROM (
                SELECT id,
                       ROW_NUMBER() OVER (
                           PARTITION BY symbol, processed_at
                           ORDER BY id ASC
                       ) as rn
                FROM real_time_prices
            ) t
            WHERE rn > 1
        )
    """)

    deleted = cursor.rowcount
    conn.commit()
    print(f"✅ Deleted {deleted:,} duplicate records")

    # Count after
    cursor.execute("SELECT COUNT(*) FROM real_time_prices")
    after_count = cursor.fetchone()[0]
    print(f"Total records after: {after_count:,}")
    print(f"Removed: {before_count - after_count:,} records")

    # Verify no more duplicates
    cursor.execute("""
        SELECT COUNT(*) FROM (
            SELECT symbol, processed_at
            FROM real_time_prices
            GROUP BY symbol, processed_at
            HAVING COUNT(*) > 1
        ) t
    """)
    remaining_dups = cursor.fetchone()[0]

    if remaining_dups == 0:
        print("\n✅ SUCCESS: No duplicates remaining!")
    else:
        print(f"\n⚠️ WARNING: Still {remaining_dups} duplicate groups")

    cursor.close()
    conn.close()

    print("=" * 60)
    return deleted


if __name__ == "__main__":
    clean_all_duplicates()
