from src.processing.spark_streaming import SparkStreamingProcessor
from src.utils.config import Config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def main():
    processor = SparkStreamingProcessor("CryptoStreamConsumer")
    
    kafka_df = processor.read_from_kafka(
        bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
        topic="crypto_prices"
    )
    
    parsed_df = processor.parse_and_transform(kafka_df)
    
    query = parsed_df.writeStream \
        .outputMode("append") \
        .foreachBatch(processor.write_to_postgres) \
        .trigger(processingTime="10 seconds") \
        .option("checkpointLocation", "/tmp/checkpoint/") \
        .start()
    
    logger.info("Spark Streaming Consumer started. Sink to PostgreSQL.")
    query.awaitTermination()

if __name__ == "__main__":
    main()