FROM apache/spark:3.5.0-python3

USER root

ENV SPARK_HOME=/opt/spark
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH

# Install Python dependencies
RUN pip install --no-cache-dir \
    kafka-python \
    psycopg2-binary \
    python-dotenv

# Copy toàn bộ src directory
COPY src /app/src

# Copy consumer code
COPY src/streaming/spark_consumer.py /app/spark_consumer.py

WORKDIR /app

CMD ["/opt/spark/bin/spark-submit", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.7.0", \
     "spark_consumer.py"]