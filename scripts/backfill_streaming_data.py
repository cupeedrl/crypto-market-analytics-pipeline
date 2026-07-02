"""
Backfill historical data into real_time_prices
Optimized version:
- Retry when Binance rate limits (429)
- Sleep between API requests
- Sleep between coins
- Batch insert using execute_values()
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from src.utils.config import Config


def fetch_binance_klines(symbol, start_date, end_date, interval="1h"):
    """Fetch historical klines from Binance"""

    url = "https://api.binance.com/api/v3/klines"

    all_data = []

    current_start = int(datetime.strptime(start_date, "%Y-%m-%d").timestamp() * 1000)
    end_time = int(datetime.strptime(end_date, "%Y-%m-%d").timestamp() * 1000)

    while current_start < end_time:

        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": current_start,
            "limit": 1000
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            # Retry when rate limited
            if response.status_code == 429:
                print(f"⚠ Rate limit for {symbol}. Sleeping 60 seconds...")
                time.sleep(60)
                continue

            response.raise_for_status()

            data = response.json()

            if not data:
                break

            for candle in data:
                open_price = float(candle[1])
                close_price = float(candle[4])

                all_data.append({
                    "symbol": symbol,
                    "current_price": close_price,
                    "price_change_percent": (
                        (close_price - open_price) / open_price * 100
                    ),
                    "volume": float(candle[5]),
                    "processed_at": datetime.fromtimestamp(candle[0] / 1000)
                })

            current_start = data[-1][0] + 1

            # Sleep between API requests
            time.sleep(0.2)

        except Exception as e:
            print(f"❌ Error fetching {symbol}: {e}")
            break

    return pd.DataFrame(all_data)


def backfill_all_coins(start_date, end_date):

    coins = [
        "BTCUSDT",
        "ETHUSDT",
        "BNBUSDT",
        "SOLUSDT",
        "XRPUSDT",
        "ADAUSDT",
        "DOGEUSDT",
        "DOTUSDT",
        "AVAXUSDT",
        "MATICUSDT",
        "LINKUSDT",
        "LTCUSDT",
        "UNIUSDT",
        "ATOMUSDT",
        "ETCUSDT"
    ]

    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        database=Config.POSTGRES_DB
    )

    cursor = conn.cursor()

    total_inserted = 0

    try:

        for coin in coins:

            print("=" * 60)
            print(f"Fetching {coin}...")

            df = fetch_binance_klines(
                coin,
                start_date,
                end_date,
                interval="1h"
            )

            if df.empty:
                print(f"⚠ No data for {coin}")
                continue

            rows = [
                (
                    row["symbol"],
                    row["current_price"],
                    row["price_change_percent"],
                    row["volume"],
                    row["processed_at"]
                )
                for _, row in df.iterrows()
            ]

            execute_values(
                cursor,
                """
                INSERT INTO real_time_prices
                (
                    symbol,
                    current_price,
                    price_change_percent,
                    volume,
                    processed_at
                )
                VALUES %s
                ON CONFLICT DO NOTHING
                """,
                rows,
                page_size=1000
            )

            conn.commit()

            total_inserted += len(rows)

            print(f"{coin}: {len(rows):,} rows inserted")

            # Sleep between coins
            time.sleep(1)

    except Exception as e:
        conn.rollback()
        print(f"\n Database Error: {e}")

    finally:
        cursor.close()
        conn.close()

    print("=" * 60)
    print(f"🎉 Finished!")
    print(f"Total rows inserted: {total_inserted:,}")


if __name__ == "__main__":

    # Backfill from June 1 to June 25, 2026
    backfill_all_coins(
        "2026-06-01",
        "2026-06-25"
    )