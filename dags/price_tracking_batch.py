from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
import sys
import os
import pandas as pd

sys.path.insert(0, os.environ.get('AIRFLOW_HOME', '/opt/airflow'))

from src.ingestion.binance_fetcher import BinanceFetcher
from src.storage.s3_loader import S3Loader
from src.storage.postgres_loader import PostgresLoader
from src.storage.bigquery_loader import BigQueryLoader

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
}

def fetch_data(**kwargs):
    fetcher = BinanceFetcher()
    df = fetcher.fetch_top_coins(limit=10)
    
    if df.empty:
        raise ValueError("No data fetched from Binance")
    
    # Tạo cột id tự động (auto-increment)
    df['id'] = range(1, len(df) + 1)  # ← PHẢI CÓ DÒNG NÀY
    
    # Convert datetime to string for XCom serialization
    if 'fetched_at' in df.columns:
        df['fetched_at'] = df['fetched_at'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    kwargs['ti'].xcom_push(key='df', value=df.to_dict('records'))
    return len(df)

def upload_to_s3(**kwargs):
    ti = kwargs['ti']
    records = ti.xcom_pull(task_ids='fetch_data', key='df')
    
    df = pd.DataFrame(records)
    
    # Parse datetime back
    if 'fetched_at' in df.columns:
        df['fetched_at'] = pd.to_datetime(df['fetched_at'])
    
    s3_loader = S3Loader()
    s3_path = s3_loader.upload_dataframe_as_json(df, prefix="raw/binance")
    
    if not s3_path:
        raise ValueError("Failed to upload to S3")
    
    return s3_path

def load_to_postgres(**kwargs):
    ti = kwargs['ti']
    records = ti.xcom_pull(task_ids='fetch_data', key='df')
    
    df = pd.DataFrame(records)
    
    # Parse datetime back
    if 'fetched_at' in df.columns:
        df['fetched_at'] = pd.to_datetime(df['fetched_at'])
    
    pg_loader = PostgresLoader()
    pg_loader.upsert_dim_coin(df)
    pg_loader.insert_ods_metrics(df)
    
    return len(df)

def load_to_bigquery(**kwargs):
    ti = kwargs['ti']
    records = ti.xcom_pull(task_ids='fetch_data', key='df')
    
    df = pd.DataFrame(records)
    
    # Parse datetime back
    if 'fetched_at' in df.columns:
        df['fetched_at'] = pd.to_datetime(df['fetched_at'])
    
    bq_loader = BigQueryLoader()
    bq_loader.load_dataframe(df, table_id='ods_daily_metrics', if_exists='append')
    
    return len(df)

with DAG(
    'crypto_price_tracking_batch',
    default_args=default_args,
    description='End-to-End Batch Pipeline: Binance -> S3 -> Postgres -> BigQuery -> dbt',
    schedule_interval='@daily',
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,  # ← Thêm dòng này
    tags=['crypto', 'batch', 'end-to-end'],
) as dag:
    
    task_fetch = PythonOperator(task_id='fetch_data', python_callable=fetch_data)
    task_upload_s3 = PythonOperator(task_id='upload_to_s3', python_callable=upload_to_s3)
    task_load_postgres = PythonOperator(task_id='load_to_postgres', python_callable=load_to_postgres)
    task_load_bigquery = PythonOperator(task_id='load_to_bigquery', python_callable=load_to_bigquery)
    
    dbt_project_path = '/opt/airflow/dbt_project/crypto_dbt'
    task_dbt_run = BashOperator(
        task_id='dbt_run',
        bash_command=f'cd {dbt_project_path} && dbt run --profiles-dir .',
    )

    task_fetch >> task_upload_s3 >> task_load_postgres >> task_load_bigquery >> task_dbt_run