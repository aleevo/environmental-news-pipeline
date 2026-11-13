
import os

import polars as pl
from kafka import KafkaConsumer

from ingest_rss import upload_to_azure


# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "172.18.0.1:9092"
)

KAFKA_TOPIC = "environmental_news"
KAFKA_GROUP_ID = "environmental_news_to_azure"

BATCH_SIZE = 100


def main():

    # 1. Create Kafka Consumer
    consumer = KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=KAFKA_GROUP_ID,
        auto_offset_reset="earliest",
        enable_auto_commit=False,
        value_deserializer=lambda value: __import__("json").loads(
            value.decode("utf-8")
        ),
        max_poll_records=BATCH_SIZE
    )

    print("Kafka consumer started...")
    print(f"Listening to topic: {KAFKA_TOPIC}")

    try:
        while True:

            # 2. Retrieve a batch of messages
            records = consumer.poll(
                timeout_ms=5000,
                max_records=BATCH_SIZE
            )

            if not records:
                continue

            articles = []

            for partition_messages in records.values():
                for message in partition_messages:

                    article = message.value

                    # Standardize article fields
                    articles.append({
                        "source": article.get("source"),
                        "title": article.get("title"),
                        "summary": article.get("summary"),
                        "clean_url": (
                            article.get("clean_url")
                            or article.get("url")
                        ),
                        "published_at": (
                            article.get("published_at")
                            or article.get("published")
                        ),
                        "ingested_at": article.get("ingested_at")
                    })

            # 3. Convert messages into a Polars DataFrame
            df = pl.DataFrame(articles)

            print(f"\nReceived {len(articles)} articles from Kafka.")
            print("Uploading batch to Azure...")

            # 4. Upload the batch to Azure as Parquet
            upload_to_azure(df)

            # 5. Commit offsets only after successful upload
            consumer.commit()

            print("Batch successfully uploaded and offsets committed!")

    except KeyboardInterrupt:
        print("\nConsumer stopped by user.")

    finally:
        consumer.close()
        print("Kafka consumer connection closed.")


if __name__ == "__main__":
    main()
