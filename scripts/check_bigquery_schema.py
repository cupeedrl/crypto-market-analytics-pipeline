from google.cloud import bigquery

client = bigquery.Client(project="stoked-jigsaw-499318-k5")

# List datasets
print("=== DATASETS ===")
datasets = list(client.list_datasets())
for dataset in datasets:
    print(f"\n📁 {dataset.dataset_id}")

    # List tables
    tables = list(client.list_tables(dataset.reference))
    for table in tables:
        print(f"\n  📊 Table: {table.table_id}")

        # Get table schema
        table_ref = dataset.table(table.table_id)
        table_obj = client.get_table(table_ref)

        print(f"  Rows: {table_obj.num_rows:,}")
        print(f"  Schema:")
        for field in table_obj.schema:
            print(f"    - {field.name}: {field.field_type} ({field.mode})")

        # Sample data
        print(f"  Sample (3 rows):")
        rows = client.list_rows(table_ref, max_results=3)
        for row in rows:
            print(f"    {dict(row)}")
