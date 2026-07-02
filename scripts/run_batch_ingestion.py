import sys
from dotenv import load_dotenv
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.binance_fetcher import BinanceFetcher
from src.storage.s3_loader import S3Loader
from src.storage.postgres_loader import PostgresLoader
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Starting Batch Ingestion Pipeline...")

    # 1. Fetch data
    fetcher = BinanceFetcher()
    df = fetcher.fetch_top_coins(limit=10)

    if df.empty:
        logger.error("No data fetched. Exiting.")
        return

    # 2. Upload to S3
    s3_loader = S3Loader()
    s3_path = s3_loader.upload_dataframe_as_json(df, prefix="raw/binance")

    # 3. Load to PostgreSQL
    pg_loader = PostgresLoader()
    pg_loader.upsert_dim_coin(df)
    pg_loader.insert_ods_metrics(df)

    logger.info("Batch Ingestion Pipeline completed successfully!")


if __name__ == "__main__":
    main()
