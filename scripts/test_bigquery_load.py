import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.storage.postgres_loader import PostgresLoader
from src.storage.bigquery_loader import BigQueryLoader
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    logger.info("Starting PostgreSQL to BigQuery load test...")
    
    # 1. Lấy dữ liệu từ PostgreSQL
    pg_loader = PostgresLoader()
    query = """
        SELECT 
            m.id,
            m.coin_id,
            c.coin_name,
            c.symbol,
            m.current_price,
            m.market_cap,
            m.total_volume,
            m.price_change_24h,
            m.price_change_percent_24h,
            m.fetched_at
        FROM ods_daily_metrics m
        JOIN dim_coin c ON m.coin_id = c.coin_id
        ORDER BY m.fetched_at DESC
        LIMIT 100;
    """
    
    logger.info("Fetching data from PostgreSQL...")
    records = pg_loader.execute_query(query, fetch=True)
    df = pd.DataFrame(records)
    
    if df.empty:
        logger.error("No data fetched from PostgreSQL.")
        return
        
    logger.info(f"Fetched {len(df)} records from PostgreSQL.")
    
    # 2. Load lên BigQuery
    bq_loader = BigQueryLoader()
    logger.info("Loading data to BigQuery...")
    bq_loader.load_dataframe(df, table_id='ods_daily_metrics', if_exists='append')
    
    logger.info("BigQuery load test completed successfully!")

if __name__ == "__main__":
    main()