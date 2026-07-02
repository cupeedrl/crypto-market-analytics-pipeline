# Streaming Pipeline

## Overview

The streaming pipeline delivers real-time cryptocurrency price updates for monitoring, analytics, and alerting. It continuously consumes Binance WebSocket events, processes them with Spark Structured Streaming, and stores aggregated results in PostgreSQL.

![Streaming Pipeline](../images/streaming-pipeline.png)

---

## Data Flow

```
Binance WebSocket
        ↓
   Kafka Producer
        ↓
   Apache Kafka
        ↓
Spark Structured Streaming
        ↓
   PostgreSQL
        ↓
Dashboard & Alerts
```

The entire pipeline is designed to provide low-latency updates while remaining fault tolerant.

---

## Message Broker

### Why Kafka?

Kafka was selected because it provides several advantages over traditional message queues:

| Feature | Kafka | RabbitMQ |
|---------|--------|----------|
| Message Replay | ✅ | ❌ |
| Horizontal Scaling | ✅ | Limited |
| Spark Integration | Excellent | Limited |

Key benefits include:

- durable event log
- replay capability for recovery
- native Spark integration
- partition-based scalability

Messages are published to a single topic:

```
crypto_prices
```

Each cryptocurrency symbol is used as the partition key, ensuring events for the same asset remain in chronological order.

---

## Stream Processing

Spark Structured Streaming consumes Kafka messages and aggregates incoming events using a **10-second tumbling window**.

Design considerations:

- balances latency and throughput
- reduces database writes
- smooths noisy price fluctuations

A watermark of **10 seconds** is applied to tolerate small network delays while preventing unlimited state growth.

Checkpointing is enabled so the stream can recover automatically after failures without reprocessing all historical messages.

---

## Storage

Processed data is written into PostgreSQL using **foreachBatch**, allowing batch inserts instead of individual writes.

Reasons for choosing PostgreSQL:

- ACID guarantees
- fast indexed queries
- seamless integration with the Streamlit dashboard
- simple SQL-based analytics

---

## Operational Challenges

Several production issues were considered during implementation:

| Challenge | Solution |
|-----------|----------|
| WebSocket disconnections | Automatic reconnect with retry |
| Duplicate messages | Composite key deduplication |
| High write throughput | Window aggregation + batch writes |
| Late events | Spark watermarking |

These mechanisms improve reliability without significantly increasing system complexity.

---

## Future Improvements

Potential enhancements include:

- Kafka Schema Registry
- Redis cache for latest prices
- ClickHouse for high-volume analytics
- End-to-end exactly-once processing