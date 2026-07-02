# Architecture Overview

This project implements a **Lambda Architecture** combining batch and streaming pipelines to achieve both accuracy and low-latency analytics.
<img width="1366" height="772" alt="image" src="https://github.com/user-attachments/assets/ade55150-bdb1-4036-b480-84e283da52e1" />

### Why Lambda Architecture?

Cryptocurrency markets operate 24/7 with high volatility. A pure batch system would introduce unacceptable latency, while a pure streaming system risks data loss during failures.

**Lambda Architecture provides:**
- **Speed Layer (Streaming)**: Real-time price updates with sub-second latency
- **Batch Layer**: Accurate historical analytics with comprehensive data
- **Serving Layer**: Unified dashboard combining both data sources

### Batch vs Streaming Trade-offs

| Aspect | Batch Pipeline | Streaming Pipeline |
|--------|----------------|-------------------|
| Latency | Hours | Sub-second |
| Throughput | High | Moderate |
| Data Accuracy | Exact | Eventually consistent |
| Use Case | Historical analysis | Real-time monitoring |

## Component Interaction

### Architecture Diagram
```mermaid
---
config:
  flowchart:
    curve: stepBefore
---
flowchart LR

%%=========================================
%% DATA SOURCES
%%=========================================
subgraph DS["📡 Data Sources"]

REST["Binance REST API<br/>Daily Klines"]

WS["Binance WebSocket<br/>24hr Ticker"]

end

%%=========================================
%% INGESTION
%%=========================================
subgraph ING["📥 Ingestion Layer"]

PY["Python Fetcher"]

KAFKA["Apache Kafka<br/>Message Broker"]

end

%%=========================================
%% PROCESSING
%%=========================================
subgraph PROC["⚙️ Processing Layer"]

AF["Apache Airflow<br/>Orchestrator"]

SPARK["Spark Structured Streaming"]

DBT["dbt<br/>Star Schema"]

end

%%=========================================
%% STORAGE
%%=========================================
subgraph STORAGE["💾 Storage Layer"]

S3["Amazon S3<br/>Raw Data Lake"]

PGODS["PostgreSQL<br/>ODS Layer"]

BQ["BigQuery<br/>Data Warehouse"]

PGRT["PostgreSQL<br/>real_time_prices"]

end

%%=========================================
%% SERVING
%%=========================================
subgraph SERVE["📊 Serving Layer"]

PBI["Streamlit Dashboard"]

DISCORD["Discord Alerts"]

end

%%=========================================
%% Batch Pipeline
%%=========================================

REST -->|"Daily OHLCV"| PY

AF -.->|"Trigger Batch"| PY

PY -->|"Archive Raw JSON"| S3

PY -->|"Load ODS"| PGODS

PY -->|"Load DW"| BQ

AF -.->|"Run dbt"| DBT

BQ -->|"Transform"| DBT

DBT -->|"Analytics"| PBI

%%=========================================
%% Streaming Pipeline
%%=========================================

WS -->|"24hr Ticker"| KAFKA

KAFKA -->|"Consume"| SPARK

SPARK -->|"Write Stream"| PGRT

AF -.->|"Query every 5 min"| PGRT

AF -->|"Send Alert"| DISCORD
```
## Data Flow Summary

### Batch Pipeline (Daily)

1. **Ingestion**: Airflow triggers daily at 00:00 UTC
2. **Fetch**: Python fetcher retrieves 24h historical data from Binance REST API
3. **Stage**: Raw JSON uploaded to S3
4. **Load**: Data copied to BigQuery staging tables
5. **Transform**: dbt models transform raw data into star schema
6. **Serve**: Dashboard queries BigQuery for historical analytics

### Streaming Pipeline (Real-time)

1. **Ingestion**: WebSocket client subscribes to 15 crypto tickers
2. **Publish**: Messages sent to Kafka topic `crypto_prices`
3. **Process**: Spark Structured Streaming consumes with 10s tumbling windows
4. **Sink**: Aggregated data written to PostgreSQL
5. **Serve**: Dashboard queries PostgreSQL for real-time KPIs

### Alert Pipeline (Every 5 min)

1. **Trigger**: Airflow DAG runs every 5 minutes
2. **Query**: PostgreSQL queried for price changes in last hour
3. **Detect**: If price change > 5%, alert triggered
4. **Notify**: Discord webhook sends formatted message

## Design Decisions

### Why PostgreSQL for Streaming?

PostgreSQL provides ACID guarantees and complex SQL analytics. While NoSQL options offer higher write throughput, they lack the SQL features required for correlation analysis.

### Why BigQuery for Batch?

BigQuery's columnar storage enables cost-effective storage of historical data with sub-second query performance. Separation from PostgreSQL prevents batch workloads from impacting real-time latency.

### Why Kafka over RabbitMQ?

Kafka's log-based architecture provides message replay capability essential for stream processing. Spark Structured Streaming requires exactly-once semantics, which Kafka's consumer groups provide natively.

### Why dbt?

dbt provides version-controlled SQL transformations with built-in testing and lineage tracking, reducing maintenance compared to custom Python ETL scripts.
