import os
import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Explicit schema để PyArrow không tự infer type sai
BQ_SCHEMA = [
    bigquery.SchemaField("id", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("coin_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("coin_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("symbol", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("current_price", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("market_cap", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("total_volume", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("price_change_24h", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("price_change_percent_24h", "FLOAT", mode="NULLABLE"),
    bigquery.SchemaField("fetched_at", "TIMESTAMP", mode="REQUIRED"),
]


class BigQueryLoader:
    def __init__(self):
        self.project_id = Config.BIGQUERY_PROJECT_ID
        self.dataset_id = Config.BIGQUERY_DATASET

        credentials_path = os.path.abspath(Config.GOOGLE_APPLICATION_CREDENTIALS)
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=["https://www.googleapis.com/auth/bigquery"]
        )

        self.client = bigquery.Client(project=self.project_id, credentials=credentials)
        self.dataset_ref = f"{self.project_id}.{self.dataset_id}"

    def load_dataframe(
        self, df: pd.DataFrame, table_id: str, if_exists: str = "append"
    ):
        """Load DataFrame vào BigQuery với explicit schema"""
        if df.empty:
            logger.warning("DataFrame is empty. Skipping BigQuery load.")
            return

        full_table_id = f"{self.dataset_ref}.{table_id}"

        try:
            # Đảm bảo cột id là integer
            if "id" in df.columns:
                df["id"] = pd.to_numeric(df["id"], errors="coerce").astype("Int64")

            # Đảm bảo fetched_at là datetime
            if "fetched_at" in df.columns:
                df["fetched_at"] = pd.to_datetime(df["fetched_at"])

            # Map if_exists parameter to BigQuery write disposition
            if if_exists == "replace":
                write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            elif if_exists == "fail":
                write_disposition = bigquery.WriteDisposition.WRITE_EMPTY
            else:  # 'append' là default
                write_disposition = bigquery.WriteDisposition.WRITE_APPEND

            # Cấu hình job load với explicit schema
            job_config = bigquery.LoadJobConfig(
                write_disposition=write_disposition,
                schema=BQ_SCHEMA,
                source_format=bigquery.SourceFormat.PARQUET,
            )

            # Load từ DataFrame
            job = self.client.load_table_from_dataframe(
                df, full_table_id, job_config=job_config, location="asia-southeast1"
            )

            # Chờ job hoàn tất
            job.result()

            logger.info(f"Successfully loaded {len(df)} rows to {full_table_id}")

        except Exception as e:
            logger.error(f"Failed to load data to BigQuery: {e}")
            raise

    def upsert_dataframe(self, df, table_id, unique_key=["coin_id", "fetched_at"]):
        """Upsert data vào BigQuery (thêm mới hoặc cập nhật)"""
        from google.cloud import bigquery

        client = bigquery.Client()
        dataset_id = os.getenv("BIGQUERY_DATASET", "crypto_analytics")
        full_table_id = f"{client.project}.{dataset_id}.{table_id}"

        # Tạo temporary table
        temp_table_id = f"{full_table_id}_temp"

        # Load data vào temp table
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE", autodetect=True
        )
        job = client.load_table_from_dataframe(df, temp_table_id, job_config=job_config)
        job.result()

        # MERGE statement
        merge_query = f"""
            MERGE `{full_table_id}` T
            USING `{temp_table_id}` S
            ON T.coin_id = S.coin_id AND T.fetched_at = S.fetched_at
            WHEN MATCHED THEN
                UPDATE SET 
                    current_price = S.current_price,
                    market_cap = S.market_cap,
                    total_volume = S.total_volume,
                    price_change_24h = S.price_change_24h,
                    price_change_percent_24h = S.price_change_percent_24h
            WHEN NOT MATCHED THEN
                INSERT (id, coin_id, current_price, market_cap, total_volume, 
                    price_change_24h, price_change_percent_24h, fetched_at)
                VALUES (S.id, S.coin_id, S.current_price, S.market_cap, S.total_volume,
                    S.price_change_24h, S.price_change_percent_24h, S.fetched_at)
        """

        query_job = client.query(merge_query)
        query_job.result()

        # Xóa temp table
        client.delete_table(temp_table_id)

        return len(df)
