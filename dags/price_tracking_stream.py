import sys
import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

# Fix: Thêm thư mục gốc của project vào Python path
# __file__ đang là /opt/airflow/dags/price_tracking_stream.py
# dirname(dirname(__file__)) sẽ ra /opt/airflow
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Bây giờ Python mới tìm thấy thư mục src
from src.alerting.price_monitor import PriceMonitor
from src.alerting.discord_notifier import DiscordNotifier

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1)
}

def monitor_prices(**kwargs):
    monitor = PriceMonitor()
    notifier = DiscordNotifier()
    
    alerts = monitor.check_price_changes(hours=1)
    
    if alerts:
        success = notifier.send_alert(alerts)
        print(f"Sent {len(alerts)} alerts to Discord. Success: {success}")
    else:
        print("No significant price changes detected")
    
    return len(alerts)

def send_daily_summary(**kwargs):
    monitor = PriceMonitor()
    notifier = DiscordNotifier()
    
    top_movers = monitor.get_top_movers(limit=5)
    
    if top_movers:
        success = notifier.send_daily_summary(top_movers)
        print(f"Sent daily summary to Discord. Success: {success}")
    
    return len(top_movers)

with DAG(
    'crypto_price_alerts',
    default_args=default_args,
    description='Monitor crypto prices and send Discord alerts',
    schedule_interval='*/5 * * * *',
    start_date=datetime(2026, 6, 15),
    catchup=False,
    tags=['streaming', 'alerts']
) as dag:
    
    monitor_task = PythonOperator(
        task_id='monitor_prices',
        python_callable=monitor_prices,
    )
    
    daily_summary_task = PythonOperator(
        task_id='daily_summary',
        python_callable=send_daily_summary,
    )
    
    monitor_task