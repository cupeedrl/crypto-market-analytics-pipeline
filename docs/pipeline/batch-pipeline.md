# Batch Pipeline

## Overview

The batch pipeline collects historical cryptocurrency market data from the Binance REST API once per day. It acts as the **batch layer** in the hybrid architecture, providing reliable historical data for analytics, reporting, and dimensional modeling.

## TaskGroup Architecture

The DAG uses TaskGroups to organize related tasks:

- **data_ingestion**: fetch_data → upload_to_s3
- **data_storage**: load_to_postgres → load_to_bigquery
- **dbt_run**: Standalone transformation task

This improves visualization and maintainability.

## Orchestration

**Tasks with TaskGroups:**

| TaskGroup | Tasks | Purpose |
|-----------|-------|---------|
| data_ingestion | fetch_data, upload_to_s3 | Fetch from Binance, store raw data |
| data_storage | load_to_postgres, load_to_bigquery | Load to databases |
| (standalone) | dbt_run | Transform with dbt |

**Production Features:**
- **Retries**: 3-5 attempts per task
- **SLA**: 1-hour completion target
- **Timeout**: 30 minutes per task
- **Alerts**: Discord notifications on success/failure
- **Logging**: Structured logs with performance metrics
---

## Data Flow

```
Binance REST API
        ↓
 Python Fetcher (Airflow)
        ↓
      Amazon S3
        ↓
 BigQuery (Staging)
        ↓
      dbt Models
        ↓
 Analytics Dashboard
```

The pipeline is orchestrated by Apache Airflow and executes once per day. Each execution processes a single date partition to ensure deterministic and repeatable results.

---

## Data Ingestion

Historical OHLCV data is collected using the Binance REST API.

Key design decisions:

- Use **1-hour candles** to balance storage cost and analytical accuracy.
- Fetch data through **pagination** with up to 1000 records per request.
- Implement retry logic with exponential backoff to handle temporary API failures.
- Process one execution date per DAG run to simplify backfilling.

The pipeline is designed to be **idempotent**, allowing failed executions to be safely re-run without generating duplicate data.

---

## Storage Strategy

### Amazon S3

S3 serves as the raw data lake.

Reasons for choosing S3:

- inexpensive long-term storage
- immutable raw data archive
- supports JSON and future file formats
- separates ingestion from downstream processing

Raw files are partitioned by date to simplify lifecycle management and historical backfills.

### Google BigQuery

BigQuery is used as the analytical warehouse.

Reasons for choosing BigQuery:

- serverless architecture
- fast analytical queries
- native integration with dbt
- automatic scaling without infrastructure management

Batch data is loaded into staging tables before being transformed into analytics models.

---

## Orchestration

Apache Airflow coordinates the entire workflow.

```
Fetch Data
      ↓
 Upload to S3
      ↓
 Load to BigQuery
      ↓
 Execute dbt Models
```

Task dependencies ensure downstream steps execute only after upstream data is successfully completed.

Airflow retries transient failures automatically and supports historical backfills through execution-date parameterization.

---

## Challenges

During development, several operational challenges were addressed:

- Binance API rate limits
- intermittent network failures
- duplicate executions after task retries
- maintaining historical consistency during backfills

These were mitigated through retry policies, idempotent loading, and date-partitioned processing.

---

## Future Improvements

- Parallel symbol ingestion using Airflow TaskGroups
- Automated data quality validation with Great Expectations
- Incremental loading strategy for warehouse tables
- Pipeline monitoring with Prometheus and Grafana
