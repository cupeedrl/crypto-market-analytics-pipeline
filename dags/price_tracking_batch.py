from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup
from airflow.exceptions import AirflowException
import sys
import os
import pandas as pd
import time
import logging

sys.path.insert(0, os.environ.get("AIRFLOW_HOME", "/opt/airflow"))

from src.ingestion.binance_fetcher import BinanceFetcher
from src.storage.s3_loader import S3Loader
from src.storage.postgres_loader import PostgresLoader
from src.storage.bigquery_loader import BigQueryLoader
from src.alerting.airflow_notifier import send_failure_alert, send_success_alert
from src.utils.logger import get_logger

logger = get_logger(__name__)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": True,
    "email_on_retry": True,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "sla": timedelta(hours=1),
    "execution_timeout": timedelta(minutes=30),
    "on_failure_callback": send_failure_alert,
    "on_success_callback": send_success_alert,
}


def fetch_data(**kwargs):
    """Fetch data from Binance with logging and metrics"""
    ti = kwargs["ti"]
    start_time = time.time()

    try:
        logger.info("Starting data fetch from Binance", extra={"limit": 10})
        fetcher = BinanceFetcher()
        df = fetcher.fetch_top_coins(limit=10)

        if df.empty:
            error_msg = "No data fetched from Binance"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Create composite ID
        df["id"] = df.apply(
            lambda row: f"{row.get('coin_id', 'unknown')}_{row['fetched_at'].strftime('%Y%m%d_%H%M%S')}",
            axis=1,
        )

        # Convert datetime to string for XCom
        if "fetched_at" in df.columns:
            df["fetched_at"] = df["fetched_at"].dt.strftime("%Y-%m-%d %H:%M:%S")

        duration = time.time() - start_time
        logger.info(
            f"Successfully fetched {len(df)} records in {duration:.2f}s",
            extra={"records": len(df), "duration": duration},
        )

        kwargs["ti"].xcom_push(key="df", value=df.to_dict("records"))
        return len(df)

    except Exception as e:
        logger.error(f"Fetch data failed: {str(e)}", exc_info=True)
        raise


def upload_to_s3(**kwargs):
    """Upload to S3 with error handling"""
    ti = kwargs["ti"]
    start_time = time.time()

    try:
        logger.info("Starting S3 upload")
        # FIXED: TaskGroup prefix
        records = ti.xcom_pull(task_ids="data_ingestion.fetch_data", key="df")

        df = pd.DataFrame(records)

        if "fetched_at" in df.columns:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"])

        s3_loader = S3Loader()
        s3_path = s3_loader.upload_dataframe_as_json(df, prefix="raw/binance")

        if not s3_path:
            raise ValueError("Failed to upload to S3 - returned empty path")

        duration = time.time() - start_time
        logger.info(f"Successfully uploaded to {s3_path} in {duration:.2f}s")
        return s3_path

    except Exception as e:
        logger.error(f"S3 upload failed: {str(e)}", exc_info=True)
        raise


def load_to_postgres(**kwargs):
    """Load to PostgreSQL with metrics"""
    ti = kwargs["ti"]
    start_time = time.time()

    try:
        logger.info("Starting PostgreSQL load")
        # FIXED: TaskGroup prefix
        records = ti.xcom_pull(task_ids="data_ingestion.fetch_data", key="df")

        df = pd.DataFrame(records)

        if "fetched_at" in df.columns:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"])

        pg_loader = PostgresLoader()
        pg_loader.upsert_dim_coin(df)
        pg_loader.insert_ods_metrics(df)

        duration = time.time() - start_time
        logger.info(
            f"Successfully loaded {len(df)} records to PostgreSQL in {duration:.2f}s"
        )
        return len(df)

    except Exception as e:
        logger.error(f"PostgreSQL load failed: {str(e)}", exc_info=True)
        raise


def load_to_bigquery(**kwargs):
    """Load to BigQuery with idempotency"""
    ti = kwargs["ti"]
    start_time = time.time()

    try:
        logger.info("Starting BigQuery load")
        # FIXED: TaskGroup prefix
        records = ti.xcom_pull(task_ids="data_ingestion.fetch_data", key="df")

        df = pd.DataFrame(records)

        if "fetched_at" in df.columns:
            df["fetched_at"] = pd.to_datetime(df["fetched_at"])

        bq_loader = BigQueryLoader()
        bq_loader.load_dataframe(df, table_id="ods_daily_metrics", if_exists="replace")

        duration = time.time() - start_time
        logger.info(
            f"Successfully loaded {len(df)} records to BigQuery in {duration:.2f}s"
        )
        return len(df)

    except Exception as e:
        logger.error(f"BigQuery load failed: {str(e)}", exc_info=True)
        raise


with DAG(
    "crypto_price_tracking_batch",
    default_args=default_args,
    description="End-to-End Batch Pipeline: Binance -> S3 -> Postgres -> BigQuery -> dbt",
    schedule_interval="@daily",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=4,
    tags=["crypto", "batch", "production", "end-to-end"],
) as dag:

    # TaskGroup: Data Ingestion
    with TaskGroup(
        "data_ingestion", tooltip="Fetch and store raw data"
    ) as ingestion_group:
        fetch_data_task = PythonOperator(
            task_id="fetch_data",
            python_callable=fetch_data,
            provide_context=True,
            retries=5,
            retry_delay=timedelta(minutes=2),
        )

        upload_s3_task = PythonOperator(
            task_id="upload_to_s3",
            python_callable=upload_to_s3,
            provide_context=True,
        )

        fetch_data_task >> upload_s3_task

    # TaskGroup: Data Storage
    with TaskGroup("data_storage", tooltip="Load data to databases") as storage_group:
        load_postgres_task = PythonOperator(
            task_id="load_to_postgres",
            python_callable=load_to_postgres,
            provide_context=True,
        )

        load_bigquery_task = PythonOperator(
            task_id="load_to_bigquery",
            python_callable=load_to_bigquery,
            provide_context=True,
        )

        load_postgres_task >> load_bigquery_task

    # dbt Transformation
    dbt_run_task = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project/crypto_dbt && dbt run --profiles-dir .",
        env={
            "GOOGLE_APPLICATION_CREDENTIALS": "/opt/airflow/gcp-service-account.json",
            **os.environ,
        },
        retries=2,
        retry_delay=timedelta(minutes=3),
    )

    # Define dependencies
    ingestion_group >> storage_group >> dbt_run_task

    # Add SLA miss callback
    def sla_miss_callback(dag, task_list, blocking_task_list, slas, blocking_tis):
        """Alert on SLA miss"""
        logger.warning(
            f"SLA missed for DAG {dag.dag_id}. " f"Blocking tasks: {blocking_task_list}"
        )
        send_failure_alert(
            {
                "dag": dag,
                "task": blocking_task_list[0] if blocking_task_list else None,
                "execution_date": datetime.now(),
                "dag_run": type("obj", (object,), {"run_id": "sla_miss"})(),
            }
        )
