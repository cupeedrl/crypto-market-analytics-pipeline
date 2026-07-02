# Alert System

## Overview

The alert system continuously monitors real-time cryptocurrency prices and automatically sends Discord notifications when significant market movements are detected.

<img width="1919" height="1036" alt="image" src="https://github.com/user-attachments/assets/f8cb4523-f924-4ca0-8b77-9b0e7b35fa3a" />


---

## Detection Logic

Apache Airflow executes the monitoring workflow every **5 minutes**.

The system compares the latest price with recent historical values stored in PostgreSQL. An alert is generated when the absolute price change exceeds a predefined threshold.

Current configuration:

| Parameter | Value |
|-----------|-------|
| Check Interval | Every 5 minutes |
| Price Threshold | ±5% |
| Data Source | PostgreSQL |

The threshold is intentionally conservative to reduce alerts caused by normal market volatility.

---

## Notification Delivery

Alerts are delivered using **Discord Webhooks**.

Each notification is formatted as a Discord Embed containing:

- cryptocurrency symbol
- current price
- percentage change
- detection timestamp
- alert severity

Discord was selected because it is free, easy to integrate, and supports rich embedded messages for financial notifications.

---

## Scheduling

The monitoring DAG uses the following cron schedule:

```text
*/5 * * * *
```

Running every five minutes provides a balance between responsiveness and resource consumption while avoiding unnecessary database queries.

---

## Challenges

Several operational issues were considered during development.

| Challenge | Solution |
|-----------|----------|
| False alerts | Price threshold filtering |
| Alert flooding | Cooldown between notifications |
| Webhook rate limits | Retry mechanism with backoff |

---

## Future Improvements

Potential enhancements include:

- User-defined alert thresholds
- Multi-channel notifications (Telegram, Email)
- Volatility-based dynamic thresholds
- Alert history and acknowledgement tracking
