# Data Model Schema

## Overview

The analytical data warehouse follows a **Star Schema** design to simplify reporting and improve query performance.

![dbt Lineage](../images/dbt-lineage.png)

---

## Schema Design

The warehouse consists of one fact table and multiple dimension tables.

```
fact_daily_metrics
        │
 ┌──────┴──────┐
 │             │
dim_coin   dim_date
```

The fact table stores daily cryptocurrency metrics, while dimension tables provide descriptive information used for filtering and aggregation.

**Grain**

- One row per coin per day.

### Why Star Schema?

Star Schema was selected because it provides:

- faster analytical queries
- simple SQL joins
- better compatibility with BI tools
- efficient aggregations by date and coin

Although dimension tables introduce minor data redundancy, the performance benefits outweigh the storage cost.

---

## dbt Modeling

The warehouse follows a layered dbt structure:

```
Raw Data
    ↓
Staging Models
    ↓
Mart Models
```

Responsibilities are clearly separated:

- **Staging** performs cleaning, type conversion, and deduplication.
- **Mart** models calculate business metrics used by the dashboard.

Incremental models are used whenever possible to process only newly arrived data, reducing both execution time and BigQuery query costs.

---

## Schema Evolution

The schema is designed to support future expansion with minimal changes.

Adding a new cryptocurrency only requires:

- inserting metadata into `dim_coin`
- enabling ingestion for the new symbol

No modifications to the fact table are required.

For entirely new business metrics with different granularities, separate fact tables can be introduced instead of extending existing ones.

---

## Future Improvements

Potential improvements include:

- Slowly Changing Dimensions (SCD Type 2)
- Data Vault modeling for additional data sources
- Automated schema validation with dbt tests