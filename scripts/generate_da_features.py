import os
import psycopg2
import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Cấu hình kết nối PostgreSQL (Host port 5433 -> Container port 5432)
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5433'),
    'database': os.getenv('POSTGRES_DB', 'crypto_ods'),
    'user': os.getenv('POSTGRES_USER', 'admin'),
    'password': os.getenv('POSTGRES_PASSWORD', 'admin123')
}

class FeatureGenerator:
    def __init__(self):
        self.conn_params = DB_CONFIG
    
    def get_connection(self):
        return psycopg2.connect(**self.conn_params)
    
    def calculate_rsi(self, prices, period=14):
        """Tính toán chỉ số RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def calculate_daily_features(self, symbol, days=30):
        """Tính toán các đặc trưng hàng ngày từ bảng real_time_prices"""
        with self.get_connection() as conn:
            query = """
            SELECT 
                DATE(processed_at) as date,
                FIRST_VALUE(current_price) OVER (PARTITION BY DATE(processed_at) ORDER BY processed_at ASC) as open_price,
                LAST_VALUE(current_price) OVER (PARTITION BY DATE(processed_at) ORDER BY processed_at ASC 
                    ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as close_price,
                MAX(current_price) OVER (PARTITION BY DATE(processed_at)) as high_price,
                MIN(current_price) OVER (PARTITION BY DATE(processed_at)) as low_price,
                SUM(volume) OVER (PARTITION BY DATE(processed_at)) as total_volume
            FROM real_time_prices
            WHERE symbol = %s 
              AND processed_at >= NOW() - INTERVAL '%s days'
            ORDER BY date DESC
            """
            
            # Sử dụng DISTINCT ON để lấy 1 dòng duy nhất cho mỗi ngày, tránh duplicate do window function
            query_clean = """
            SELECT DISTINCT ON (DATE(processed_at))
                DATE(processed_at) as date,
                FIRST_VALUE(current_price) OVER w as open_price,
                LAST_VALUE(current_price) OVER w as close_price,
                MAX(current_price) OVER (PARTITION BY DATE(processed_at)) as high_price,
                MIN(current_price) OVER (PARTITION BY DATE(processed_at)) as low_price,
                SUM(volume) OVER (PARTITION BY DATE(processed_at)) as total_volume
            FROM real_time_prices
            WHERE symbol = %s 
              AND processed_at >= NOW() - INTERVAL '%s days'
            WINDOW w AS (PARTITION BY DATE(processed_at) ORDER BY processed_at ASC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)
            ORDER BY date DESC
            """
            
            df = pd.read_sql(query_clean, conn, params=(symbol, days))
            
            if len(df) < 2:
                logger.warning(f"Không đủ dữ liệu cho {symbol}. Cần ít nhất 2 ngày.")
                return None
            
            # Sắp xếp theo thời gian tăng dần để tính toán chỉ số kỹ thuật chính xác
            df = df.sort_values('date').reset_index(drop=True)
            
            # Tính toán lợi nhuận hàng ngày (Daily Return)
            df['daily_return'] = df['close_price'].pct_change() * 100
            
            # Tính toán biến động (Volatility - độ lệch chuẩn của lợi nhuận)
            df['volatility_7d'] = df['daily_return'].rolling(window=7).std()
            df['volatility_30d'] = df['daily_return'].rolling(window=30).std()
            
            # Tính toán thay đổi khối lượng
            df['volume_change_pct'] = df['total_volume'].pct_change() * 100
            
            # Tính toán RSI
            df['rsi_14'] = self.calculate_rsi(df['close_price'], period=14)
            
            # Tỷ lệ giá trên khối lượng
            df['price_to_volume_ratio'] = df['close_price'] / df['total_volume']
            
            # Sức mạnh xu hướng (độ dốc của hồi quy tuyến tính 7 ngày)
            def calc_slope(x):
                if len(x) < 7: return 0
                y = x.values
                x_idx = np.arange(len(y))
                slope, _ = np.polyfit(x_idx, y, 1)
                return slope

            df['trend_strength'] = df['close_price'].rolling(window=7).apply(calc_slope, raw=False)
            
            # Xác định xu hướng tăng/giảm
            df['is_bullish'] = df['trend_strength'] > 0
            
            df['symbol'] = symbol
            
            return df
    
    def populate_features_table(self):
        """Tạo và chèn dữ liệu vào bảng crypto_features"""
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            for symbol in symbols:
                logger.info(f"Đang tạo đặc trưng cho {symbol}...")
                df = self.calculate_daily_features(symbol, days=30)
                
                if df is None or df.empty:
                    continue
                
                # Chèn dữ liệu vào database
                for _, row in df.iterrows():
                    try:
                        # Bỏ qua các hàng có giá trị NaN ở các cột bắt buộc
                        if pd.isna(row['close_price']) or pd.isna(row['date']):
                            continue

                        cursor.execute("""
                        INSERT INTO crypto_features (
                            symbol, date, open_price, close_price, high_price, low_price,
                            daily_return, volatility_7d, volatility_30d, total_volume,
                            volume_change_pct, rsi_14, price_to_volume_ratio,
                            trend_strength, is_bullish
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (symbol, date) DO UPDATE SET
                            open_price = EXCLUDED.open_price,
                            close_price = EXCLUDED.close_price,
                            high_price = EXCLUDED.high_price,
                            low_price = EXCLUDED.low_price,
                            daily_return = EXCLUDED.daily_return,
                            volatility_7d = EXCLUDED.volatility_7d,
                            volatility_30d = EXCLUDED.volatility_30d,
                            total_volume = EXCLUDED.total_volume,
                            volume_change_pct = EXCLUDED.volume_change_pct,
                            rsi_14 = EXCLUDED.rsi_14,
                            price_to_volume_ratio = EXCLUDED.price_to_volume_ratio,
                            trend_strength = EXCLUDED.trend_strength,
                            is_bullish = EXCLUDED.is_bullish
                        """, (
                            row['symbol'], row['date'], 
                            row.get('open_price'), row['close_price'], 
                            row.get('high_price'), row.get('low_price'), 
                            row.get('daily_return'), row.get('volatility_7d'), 
                            row.get('volatility_30d'), row.get('total_volume'),
                            row.get('volume_change_pct'), row.get('rsi_14'), 
                            row.get('price_to_volume_ratio'), row.get('trend_strength'), 
                            row.get('is_bullish')
                        ))
                    except Exception as e:
                        logger.error(f"Lỗi khi chèn {symbol} ngày {row['date']}: {e}")
                        conn.rollback()
                        continue
                    
                    conn.commit()
            
            cursor.close()
            logger.info("Hoàn tất tạo đặc trưng cho tất cả symbols.")

if __name__ == "__main__":
    generator = FeatureGenerator()
    generator.populate_features_table()