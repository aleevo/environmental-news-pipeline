import os
import feedparser
import pandas as pd
import polars as pl
from datetime import datetime, timezone
from azure.storage.blob import BlobServiceClient
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv() 

# --- CONFIGURATION ---
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
if not AZURE_CONNECTION_STRING:
    print(" ERROR: AZURE_STORAGE_CONNECTION_STRING is missing!")
    exit(1)

CONTAINER_NAME = "primary" 

# --- 1. THE 10 SOURCES ---
RSS_FEEDS = {
    "eea": "https://www.eea.europa.eu/en/newsroom/newsletter/eea-press-releases-rss-feed/rss.xml",
    "ec_eu": "https://environment.ec.europa.eu/node/686/rss_en",
    "clean_energy_wire": "https://www.cleanenergywire.org/rss.xml",
    "dw": "https://rss.dw.com/xml/rss_en_environment",
    "dialogue_earth": "https://dialogue.earth/en/feed/",
    "cgtn_china": "https://www.cgtn.com/subscribe/rss/section/china.xml", 
    "carbon_brief": "https://www.carbonbrief.org/feed",
    "mongabay": "https://news.mongabay.com/feed/",
    "sciencedaily": "https://www.sciencedaily.com/rss/earth_climate.xml",
    "nasa": "https://www.nasa.gov/news-release/feed/"
}

# Keywords to filter CGTN (and only CGTN, since it's general news)
ENV_KEYWORDS = [
    "environment", "climate", "pollution", "solar energy", "green", 
    "sustainability", "carbon emissions", "conservation", "wind energy", # <-- Fixed!
    "wildlife", "water", "renewable energy", "ecosystem", "biodiversity"
]

def is_environmental(title, summary):
    """Helper function to check if an article is about the environment."""
    # Combine title and summary, make it lowercase for matching
    text_to_check = (title + " " + summary).lower()
    # Return True if any keyword is found in the text
    return any(keyword in text_to_check for keyword in ENV_KEYWORDS)

def fetch_articles():
    articles = []
    # Using a User-Agent header prevents many sites from blocking the script as a bot
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for source_name, url in RSS_FEEDS.items():
        print(f"Fetching from {source_name}...")
        try:
            # Use feedparser with the agent parameter
            feed = feedparser.parse(url, agent=headers["User-Agent"])
            
            if feed.bozo == 1 and len(feed.entries) == 0:
                print(f"  [Warning] Failed to parse feed for {source_name}.")
                continue

            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", entry.get("description", ""))
                
                # --- FILTERING LOGIC ---
                if source_name == "cgtn_china" and not is_environmental(title, summary):
                    continue 

                # --- DATE PARSING LOGIC ---
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    # Convert the parsed time struct to a timezone-aware ISO string
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
                else:
                    # Fallback if the feed has no published date
                    pub_date = datetime.now(timezone.utc).isoformat()

                articles.append({
                    "source": source_name,
                    "title": title,
                    "summary": summary,
                    "clean_url": entry.get("link", ""),
                    "published_at": pub_date,
                    "ingested_at": datetime.now(timezone.utc).isoformat() 
                })
        except Exception as e:
            print(f"  [Error] Could not fetch {source_name}: {e}")
            
    print(f"\nTotal articles fetched: {len(articles)}")
    return pd.DataFrame(articles)

def upload_to_azure(df):
    if df.empty:
        print("No data to upload. Exiting.")
        return

    # --- 2. POLARS TRANSFORMATION ---
    print("Converting to Polars and preparing Parquet...")
    pl_df = pl.from_pandas(df)
    
    # Write to an in-memory buffer using Polars
    parquet_buffer = io.BytesIO()
    pl_df.write_parquet(parquet_buffer)
    
    # --- 3. PARTITIONING FOR SYNAPSE ---
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
    
    now = datetime.now(timezone.utc)
    current_time_str = now.strftime("%H%M%S")
    
    # Create the Hive-style partition path
    blob_name = f"raw_news/year={now.year}/month={now.month:02d}/day={now.day:02d}/news_batch_{current_time_str}.parquet"
    
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    
    print(f"Uploading to Azure Storage as: {blob_name}...")
    blob_client.upload_blob(parquet_buffer.getvalue(), overwrite=True)
    print(" Upload successful!")

if __name__ == "__main__":
    print("Starting ingestion...")
    pandas_df = fetch_articles()
    upload_to_azure(pandas_df)

