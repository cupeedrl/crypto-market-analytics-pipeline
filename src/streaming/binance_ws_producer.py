from kafka import KafkaProducer
import json
from src.ingestion.websocket_client import BinanceWebSocketClient
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BinanceWSProducer:
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=[Config.KAFKA_BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.topic = "crypto_prices"

    def send_to_kafka(self, data):
        """Gửi data vào Kafka"""
        self.producer.send(self.topic, value=data)
        self.producer.flush()
        logger.info(f"Sent to Kafka: {data.get('s')} | Price: {data.get('c')}")

    def start(self):
        """Bắt đầu producer"""
        symbols = [
            "btcusdt",
            "ethusdt",
            "bnbusdt",
            "solusdt",
            "xrpusdt",
            "adausdt",
            "dogeusdt",
            "dotusdt",
            "avaxusdt",
            "polusdt",
            "linkusdt",
            "ltcusdt",
            "uniusdt",
            "atomusdt",
            "etcusdt",
        ]
        client = BinanceWebSocketClient(symbols, self.send_to_kafka)
        logger.info("Starting Binance WebSocket Producer...")
        client.start()


if __name__ == "__main__":
    producer = BinanceWSProducer()
    producer.start()
