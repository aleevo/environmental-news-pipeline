
import os
import dlt
from dotenv import load_dotenv
from dlt.sources.filesystem import filesystem, read_parquet

# 1. Load credentials and settings from .env
load_dotenv(dotenv_path=".env")

# 2. Read the Azure connection string
connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

if not connection:
    raise ValueError("Azure connection string is missing from .env")

parts = dict(
    item.split("=", 1)
    for item in connection.split(";")
    if "=" in item
)

# 3. Configure Azure credentials for dlt
os.environ["SOURCES__FILESYSTEM__CREDENTIALS__AZURE_STORAGE_ACCOUNT_NAME"] = parts["AccountName"]
os.environ["SOURCES__FILESYSTEM__CREDENTIALS__AZURE_STORAGE_ACCOUNT_KEY"] = parts["AccountKey"]

# 4. Configure PostgreSQL credentials for dlt
os.environ["DESTINATION__POSTGRES__CREDENTIALS__HOST"] = "localhost"
os.environ["DESTINATION__POSTGRES__CREDENTIALS__PORT"] = "5432"
os.environ["DESTINATION__POSTGRES__CREDENTIALS__DATABASE"] = os.getenv("POSTGRES_DB")
os.environ["DESTINATION__POSTGRES__CREDENTIALS__USERNAME"] = os.getenv("POSTGRES_USER")
os.environ["DESTINATION__POSTGRES__CREDENTIALS__PASSWORD"] = os.getenv("POSTGRES_PASSWORD")

# 5. Locate all Parquet files under raw_news/
files = filesystem(
    bucket_url="az://primary/raw_news/",
    file_glob="**/*.parquet"
)

# 6. Read the Parquet files
articles = files | read_parquet()

# 7. Create the dlt pipeline
pipeline = dlt.pipeline(
    pipeline_name="azure_news_to_postgres",
    destination="postgres",
    dataset_name="dlt_landing"
)

# 8. Load articles using clean_url as the primary key
articles.apply_hints(
    primary_key="clean_url",
    write_disposition="merge"
)

load_info = pipeline.run(
    articles,
    table_name="news_articles"
)

print(load_info)
