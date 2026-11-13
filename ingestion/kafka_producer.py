
import json
import os

from kafka import KafkaProducer
from ingest_rss import fetch_articles

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "172.18.0.1:9092"
)

KAFKA_TOPIC = "environmental_news"


def main():

    # 1. Fetch articles from RSS feeds
    print("Fetching environmental news from RSS feeds...")

    df = fetch_articles()

    if df.is_empty():
        print("No articles found. Nothing to send to Kafka.")
        return

    # 2. Convert Polars DataFrame into a list of dictionaries
    articles = df.to_dicts()

    print(f"Found {len(articles)} articles.")

    # 3. Create Kafka Producer
    producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(
            value, ensure_ascii=False
        ).encode("utf-8"),
        key_serializer=lambda key: key.encode("utf-8"),
        acks="all",
        retries=5
    )

    try:
        # 4. Send each article to Kafka
        for article in articles:

            article_key = article.get("clean_url") or article["title"]

            future = producer.send(
                KAFKA_TOPIC,
                key=article_key,
                value=article
            )

            metadata = future.get(timeout=10)

            print(
                f"Sent article: {article['title'][:60]} | "
                f"Partition: {metadata.partition} | "
                f"Offset: {metadata.offset}"
            )

        producer.flush()

        print(f"\nSuccessfully sent {len(articles)} articles to Kafka!")

    finally:
        producer.close()


if __name__ == "__main__":
    main()
