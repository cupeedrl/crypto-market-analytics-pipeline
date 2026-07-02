from pyspark.sql import SparkSession
from pyspark.sql.functions import col, get_json_object
from pyspark.sql.types import DoubleType, LongType
from src.utils.config import Config

class SparkStreamingProcessor:
    """
    Xử lý streaming data với Spark Structured Streaming
    
    Idempotency:
    - dropDuplicates() trong parse_and_transform() giúp loại bỏ duplicate trong cùng batch
    - Checkpoint location đảm bảo không đọc lại Kafka messages đã xử lý
    - Nếu cần đảm bảo 100% không duplicate, thêm unique constraint trong PostgreSQL
    """
    
    def __init__(self, app_name: str = "CryptoStreamingProcessor"):
        self.spark = SparkSession.builder \
            .appName(app_name) \
            .master("local[*]") \
            .config("spark.jars.packages", 
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,"
                    "org.postgresql:postgresql:42.7.0") \
            .getOrCreate()
        
        self.spark.sparkContext.setLogLevel("WARN")
    
    def read_from_kafka(self, bootstrap_servers: str, topic: str):
        """Đọc data từ Kafka topic"""
        kafka_df = self.spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", bootstrap_servers) \
            .option("subscribe", topic) \
            .option("startingOffsets", "latest") \
            .load()
        
        return kafka_df
    
    def parse_and_transform(self, kafka_df):
        """
        Parse JSON và transform data
        
        Idempotency: dropDuplicates() đảm bảo không có duplicate trong cùng batch
        """
        json_col = col("value").cast("string")
        
        # Dùng get_json_object để tránh ambiguous field reference
        final_df = kafka_df.select(
            get_json_object(json_col, "$.s").alias("symbol"),
            get_json_object(json_col, "$.c").cast(DoubleType()).alias("current_price"),
            get_json_object(json_col, "$.p").cast(DoubleType()).alias("price_change"),
            get_json_object(json_col, "$.P").cast(DoubleType()).alias("price_change_percent"),
            get_json_object(json_col, "$.v").cast(DoubleType()).alias("volume"),
            col("partition").alias("kafka_partition"),
            col("offset").alias("kafka_offset"),
            (get_json_object(json_col, "$.E").cast(LongType()) / 1000).cast("timestamp").alias("processed_at")
        ).dropDuplicates(["symbol", "processed_at"])  # Idempotency: loại bỏ duplicate
        
        return final_df
    
    def write_to_postgres(self, df, epoch_id):
        """Ghi data vào PostgreSQL"""
        postgres_url = f"jdbc:postgresql://{Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}/{Config.POSTGRES_DB}"
        
        row_count = df.count()
        if row_count > 0:
            try:
                # Chọn đúng cột
                df_to_write = df.select(
                    "symbol",
                    "current_price",
                    "price_change",
                    "price_change_percent",
                    "volume",
                    "processed_at",
                    "kafka_offset",
                    "kafka_partition"
                )
                
                df_to_write.write \
                    .format("jdbc") \
                    .option("url", postgres_url) \
                    .option("dbtable", "real_time_prices") \
                    .option("user", Config.POSTGRES_USER) \
                    .option("password", Config.POSTGRES_PASSWORD) \
                    .option("driver", "org.postgresql.Driver") \
                    .mode("append") \
                    .save()
                print(f"Epoch {epoch_id}: Wrote {row_count} rows to PostgreSQL")
            except Exception as e:
                print(f"ERROR in Epoch {epoch_id}: {e}")
                import traceback
                traceback.print_exc()
    
    def stop(self):
        """Stop Spark session"""
        self.spark.stop()