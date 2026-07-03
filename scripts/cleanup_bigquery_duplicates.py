from google.cloud import bigquery
import os

def cleanup_duplicates():
    client = bigquery.Client(project='stoked-jigsaw-499318-k5')
    dataset_id = 'crypto_analytics'
    table_id = f"{client.project}.{dataset_id}.ods_daily_metrics"
    
    # Tìm và xóa duplicates (giữ bản mới nhất)
    cleanup_query = f"""
        DELETE FROM `{table_id}`
        WHERE id IN (
            SELECT id
            FROM (
                SELECT id, 
                       ROW_NUMBER() OVER (
                           PARTITION BY coin_id, fetched_at 
                           ORDER BY fetched_at DESC
                       ) as rn
                FROM `{table_id}`
            )
            WHERE rn > 1
        )
    """
    
    print("Deleting duplicates...")
    query_job = client.query(cleanup_query)
    query_job.result()
    print(f"Deleted {query_job.num_dml_affected_rows} duplicate rows")
    
    # Verify
    verify_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(DISTINCT CONCAT(coin_id, '_', CAST(fetched_at AS STRING))) as unique_records
        FROM `{table_id}`
    """
    results = client.query(verify_query).result()
    for row in results:
        print(f"Total rows: {row.total_rows}, Unique records: {row.unique_records}")

if __name__ == "__main__":
    cleanup_duplicates()