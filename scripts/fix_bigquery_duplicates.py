from google.cloud import bigquery

client = bigquery.Client(project='stoked-jigsaw-499318-k5')

# Query để tìm duplicates
query = """
    DELETE FROM `crypto_analytics.ods_daily_metrics`
    WHERE id IN (
        SELECT id
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY id ORDER BY fetched_at) as rn
            FROM `crypto_analytics.ods_daily_metrics`
        )
        WHERE rn > 1
    )
"""

print("Deleting duplicates...")
query_job = client.query(query)
query_job.result()
print(f"Deleted duplicates. Rows affected: {query_job.num_dml_affected_rows}")

# Verify
verify_query = """
    SELECT COUNT(*) as total_rows,
           COUNT(DISTINCT id) as unique_ids
    FROM `crypto_analytics.ods_daily_metrics`
"""
results = client.query(verify_query).result()
for row in results:
    print(f"Total rows: {row.total_rows}, Unique IDs: {row.unique_ids}")