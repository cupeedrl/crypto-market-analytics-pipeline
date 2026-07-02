
# Deployment Setup

## Overview

The project is fully containerized using Docker Compose, ensuring consistent environments across development and deployment.

---

## Container Architecture

The system consists of several independent services:

- PostgreSQL
- Apache Airflow
- Apache Kafka
- Spark Structured Streaming
- Streamlit Dashboard

Each service runs inside its own container, simplifying deployment and dependency management.

---

## Environment Configuration

Application settings are managed through a `.env` file.

Typical configuration includes:

- PostgreSQL credentials
- AWS S3 configuration
- Google BigQuery settings
- Discord Bot and Webhook tokens

Sensitive files such as `.env` and service account credentials are excluded from Git using `.gitignore`.

Using environment variables keeps the project portable across development and production environments without modifying the source code.

---

## Running the Project

Start all services:

```bash
docker compose up -d
```

Stop all services:

```bash
docker compose down
```

Verify running containers:

```bash
docker ps
```

---

## Scaling Considerations

The architecture supports future scaling with minimal changes.

| Component | Scaling Strategy |
|-----------|------------------|
| Kafka | Add brokers and partitions |
| Spark | Add worker nodes |
| PostgreSQL | Vertical scaling |
| Streamlit | Multiple application instances behind a load balancer |

Streaming components can be scaled horizontally, while PostgreSQL is currently sufficient with vertical scaling for the expected workload.

---

## Future Improvements

Potential deployment enhancements include:

- Kubernetes deployment
- Infrastructure as Code with Terraform
- CI/CD automation using GitHub Actions
- Monitoring with Prometheus and Grafana