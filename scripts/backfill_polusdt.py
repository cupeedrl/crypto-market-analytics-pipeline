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
            "symbol": symbol.upper(),
            "interval": interval,
            "startTime": current_start,
            "limit": 1000,
        }

        try:
            response = requests.get(url, params=params, timeout=30)

            if response.status_code == 429:
                print(f"Rate limit. Sleeping 60s...")
                time.sleep(60)
                continue

            response.raise_for_status()
            data = response.json()

            if not data:
                break

            for candle in data:
                open_price = float(candle[1])
                close_price = float(candle[4])

                all_data.append(
                    {
                        "symbol": symbol.upper(),
                        "current_price": close_price,
                        "price_change_percent": (
                            (close_price - open_price) / open_price * 100
                        ),
                        "volume": float(candle[5]),
                        "processed_at": datetime.fromtimestamp(candle[0] / 1000),
                    }
                )

            current_start = data[-1][0] + 1
            time.sleep(0.2)

        except Exception as e:
            print(f"Error: {e}")
            break

    return pd.DataFrame(all_data)


def backfill_polusdt(start_date, end_date):
    """Backfill POLUSDT data"""
    conn = psycopg2.connect(
        host=Config.POSTGRES_HOST,
        port=Config.POSTGRES_PORT,
        user=Config.POSTGRES_USER,
        password=Config.POSTGRES_PASSWORD,
        database=Config.POSTGRES_DB,
    )
    cursor = conn.cursor()

    print(f"Fetching POLUSDT from {start_date} to {end_date}...")
    df = fetch_binance_klines("POLUSDT", start_date, end_date, interval="1h")

    if df.empty:
        print("No data fetched")
        return

    rows = [
        (
            row["symbol"],
            row["current_price"],
            row["price_change_percent"],
            row["volume"],
            row["processed_at"],
        )
        for _, row in df.iterrows()
    ]

    execute_values(
        cursor,
        """INSERT INTO real_time_prices 
           (symbol, current_price, price_change_percent, volume, processed_at)
           VALUES %s ON CONFLICT DO NOTHING""",
        rows,
        page_size=1000,
    )

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Inserted {len(rows):,} rows for POLUSDT")


if __name__ == "__main__":
    backfill_polusdt("2026-06-01", "2026-07-02")
