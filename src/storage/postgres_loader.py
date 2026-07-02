import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

class PostgresLoader:
    def __init__(self):
        self.conn_params = {
            "host": Config.POSTGRES_HOST,
            "port": Config.POSTGRES_PORT,
            "user": Config.POSTGRES_USER,
            "password": Config.POSTGRES_PASSWORD,
            "database": Config.POSTGRES_DB
        }

    def get_connection(self):
        return psycopg2.connect(**self.conn_params)

    def execute_query(self, query: str, params: tuple = None, fetch: bool = False):
        """Thực thi câu lệnh SQL"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(query, params)
                    if fetch:
                        return cur.fetchall()
                    conn.commit()
                    logger.info(f"Query executed. Rows affected: {cur.rowcount}")
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            raise

    def upsert_dim_coin(self, df):
        """Upsert dimension coin table - idempotent"""
        if df.empty:
            return
            
        query = """
            INSERT INTO dim_coin (coin_id, coin_name, symbol)
            VALUES %s
            ON CONFLICT (coin_id) 
            DO UPDATE SET 
                coin_name = EXCLUDED.coin_name,
                symbol = EXCLUDED.symbol,
                updated_at = CURRENT_TIMESTAMP;
        """
        data = [tuple(x) for x in df[['coin_id', 'coin_name', 'symbol']].values]
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    execute_values(cur, query, data)
                    conn.commit()
                    logger.info(f"Upserted {len(data)} records into dim_coin.")
        except psycopg2.Error as e:
            logger.error(f"Failed to upsert dim_coin: {e}")
            raise

    def insert_ods_metrics(self, df):
        """Insert ODS daily metrics with UPSERT to handle duplicates - idempotent"""
        if df.empty:
            logger.info("DataFrame is empty. Skipping insert.")
            return
            
        try:
            conn = self.get_connection()
            cur = conn.cursor()
            
            # Đảm bảo DataFrame có đúng các cột cần thiết theo schema thực tế
            required_columns = [
                'coin_id', 'fetched_at', 'current_price', 
                'market_cap', 'total_volume', 
                'price_change_24h', 'price_change_percent_24h'
            ]
            
            # Kiểm tra và lọc chỉ lấy các cột cần thiết
            df_filtered = df[required_columns].copy()
            
            # Convert DataFrame to list of tuples
            data = [tuple(row) for row in df_filtered.to_numpy()]
            
            # UPSERT query: INSERT ... ON CONFLICT DO UPDATE
            # Dùng trực tiếp columns thay vì constraint name
            query = """
                INSERT INTO ods_daily_metrics (coin_id, fetched_at, current_price, market_cap, total_volume, price_change_24h, price_change_percent_24h)
                VALUES %s
                ON CONFLICT (coin_id, date(fetched_at))
                DO UPDATE SET
                    current_price = EXCLUDED.current_price,
                    market_cap = EXCLUDED.market_cap,
                    total_volume = EXCLUDED.total_volume,
                    price_change_24h = EXCLUDED.price_change_24h,
                    price_change_percent_24h = EXCLUDED.price_change_percent_24h
            """
            
            execute_values(cur, query, data)
            conn.commit()
            
            logger.info(f"Upserted {len(df)} records into ods_daily_metrics.")
            
        except Exception as e:
            logger.error(f"Failed to upsert ods_daily_metrics: {e}")
            raise
        finally:
            cur.close()
            conn.close()