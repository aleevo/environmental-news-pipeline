import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

connect_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client("primary")

print("Scanning raw_news/ for anomalies...")

# List EVERYTHING inside raw_news
blobs = container_client.list_blobs(name_starts_with="raw_news/")

deleted_count = 0
for blob in blobs:
    # If the blob does NOT start with the correct partition name, it's the weird folder
    if not blob.name.startswith("raw_news/year="):
        print(f"Found anomaly! Deleting: {blob.name}")
        container_client.delete_blob(blob.name)
        deleted_count += 1

if deleted_count == 0:
    print("✅ No anomalies found. Your folder is clean!")
else:
    print(f"✅ Cleanup complete! Deleted {deleted_count} weird files.")
