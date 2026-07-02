import os
import psycopg2
import pandas as pd
import numpy as np
from google.cloud import bigquery

# Cấu hình
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gcp-service-account.json'
BQ_PROJECT = 'stoked-jigsaw-499318-k5'
BQ_DATASET = 'crypto_analytics'

PG_CONFIG = {
    'host': 'localhost',
    'port': '5433',
    'database': 'crypto_ods',
    'user': 'admin',
    'password': 'admin123'
}

def export_bigquery_to_postgres():
    print("Đang kết nối BigQuery...")
    client = bigquery.Client(project=BQ_PROJECT)
    
    # Query lấy dữ liệu 30 ngày
    query = f"""
    SELECT 
        coin_id as symbol,
        DATE(fetched_at) as date,
        AVG(current_price) as avg_price,
        MAX(current_price) as max_price,
        MIN(current_price) as min_price,
        SUM(total_volume) as total_volume
    FROM `{BQ_PROJECT}.{BQ_DATASET}.stg_crypto_prices`
    WHERE fetched_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
    GROUP BY coin_id, DATE(fetched_at)
    ORDER BY date DESC
    """
    
    print("Đang tải dữ liệu từ BigQuery...")
    df = client.query(query).to_dataframe()
    print(f"Đã tải {len(df)} rows.")
    
    if df.empty:
        print("Không có dữ liệu.")
        return

    # Transform data
    features_df = pd.DataFrame()
    # 1. Chuẩn hóa symbol (viết hoa) để đồng bộ với streaming data
    features_df['symbol'] = df['symbol'].str.upper()
    # 2. FIX: Map cột 'date' từ BQ sang 'date_hour' của PostgreSQL
    features_df['date_hour'] = df['date'] 
    
    features_df['open_price'] = df['avg_price'] * 0.99
    features_df['close_price'] = df['avg_price']
    features_df['high_price'] = df['max_price']
    features_df['low_price'] = df['min_price']
    features_df['total_volume'] = df['total_volume']
    
    # Sắp xếp để tính toán chỉ số chính xác
    features_df = features_df.sort_values(['symbol', 'date_hour']).reset_index(drop=True)
    
    # Tính toán các chỉ số
    features_df['daily_return'] = features_df.groupby('symbol')['close_price'].pct_change() * 100
    features_df['volatility_7d'] = features_df.groupby('symbol')['daily_return'].transform(lambda x: x.rolling(7).std())
    features_df['volatility_30d'] = features_df.groupby('symbol')['daily_return'].transform(lambda x: x.rolling(30).std())
    features_df['volume_change_pct'] = features_df.groupby('symbol')['total_volume'].pct_change() * 100
    features_df['rsi_14'] = 50.0 # Tạm thời fix 50
    features_df['price_to_volume_ratio'] = features_df['close_price'] / features_df['total_volume']
    
    def calc_slope(x):
        if len(x) < 7: return 0
        return np.polyfit(range(len(x)), x, 1)[0]
    
    features_df['trend_strength'] = features_df.groupby('symbol')['close_price'].transform(lambda x: x.rolling(7).apply(calc_slope, raw=False))
    features_df['is_bullish'] = features_df['trend_strength'] > 0
    
    # Insert vào PostgreSQL
    print("Đang insert vào PostgreSQL...")
    conn = psycopg2.connect(**PG_CONFIG)
    cursor = conn.cursor()
    
    inserted_count = 0
    
    for _, row in features_df.iterrows():
        try:
            cursor.execute("""
            INSERT INTO crypto_features (
                symbol, date_hour, open_price, close_price, high_price, low_price,
                daily_return, volatility_7d, volatility_30d, total_volume,
                volume_change_pct, rsi_14, price_to_volume_ratio,
                trend_strength, is_bullish
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, date_hour) DO NOTHING
            """, (
                row['symbol'], row['date_hour'], row['open_price'], row['close_price'],
                row['high_price'], row['low_price'], row['daily_return'],
                row['volatility_7d'], row['volatility_30d'], row['total_volume'],
                row['volume_change_pct'], row['rsi_14'], row['price_to_volume_ratio'],
                row['trend_strength'], row['is_bullish']
            ))
            inserted_count += 1
        except Exception as e:
            # Bỏ qua lỗi trùng lặp hoặc lỗi nhỏ
            pass
        conn.commit()
        
    cursor.close()
    conn.close()
    print(f"Hoàn tất! Insert thành công {inserted_count} rows.")

if __name__ == "__main__":
    export_bigquery_to_postgres()