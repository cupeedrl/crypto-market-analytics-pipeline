import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # PostgreSQL
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_USER = os.getenv("POSTGRES_USER", "admin")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "admin123")
    POSTGRES_DB = os.getenv("POSTGRES_DB", "crypto_ods")

    # AWS S3
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "crypto-data-lake")

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_TRADES = os.getenv("KAFKA_TOPIC_TRADES", "crypto_trades")

    # APIs
    COINGECKO_API_URL = os.getenv(
        "COINGECKO_API_URL", "https://api.coingecko.com/api/v3"
    )
    COINCAP_API_URL = os.getenv("COINCAP_API_URL", "https://api.coincap.io/v2")

    # Google Cloud (BigQuery)
    BIGQUERY_PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID", "")
    BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "crypto_analytics")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS", "gcp-service-account.json"
    )

    # Discord
    DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
    DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
