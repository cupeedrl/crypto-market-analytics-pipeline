import requests
import psycopg2
from google.cloud import bigquery
import sys


def check_postgres():
    try:
        conn = psycopg2.connect(
            host="localhost",
            port="5433",
            user="admin",
            password="admin123",
            database="crypto_ods"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM real_time_prices")
        count = cursor.fetchone()[0]
        print(f"PostgreSQL: {count:,} records")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"PostgreSQL: {str(e)}")
        return False


def check_bigquery():
    try:
        client = bigquery.Client(project="stoked-jigsaw-499318-k5")
        query = """
        SELECT COUNT(*) AS total
        FROM `stoked-jigsaw-499318-k5.crypto_analytics.fact_daily_metrics`
        """
        results = client.query(query).result()

        for row in results:
            print(f"BigQuery: {row.total:,} records in fact_daily_metrics")

        return True

    except Exception as e:
        print(f"BigQuery: {str(e)}")
        return False


def check_dashboard():
    try:
        response = requests.get("http://localhost:8501", timeout=5)

        if response.status_code == 200:
            print("Dashboard: Online at http://localhost:8501")
            return True
        else:
            print(f"Dashboard: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"Dashboard: {str(e)}")
        return False


def check_airflow():
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)

        if response.status_code == 200:
            print("Airflow: Online at http://localhost:8080")
            return True
        else:
            print(f"Airflow: Status {response.status_code}")
            return False

    except Exception as e:
        print(f"Airflow: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("PRODUCTION FEATURES VERIFICATION")
    print("=" * 60)

    results = [
        check_airflow(),
        check_dashboard(),
        check_postgres(),
        check_bigquery()
    ]

    print("=" * 60)

    if all(results):
        print("ALL CHECKS PASSED - Ready for portfolio!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("SOME CHECKS FAILED - Review above")
        print("=" * 60)
        sys.exit(1)