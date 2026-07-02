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
