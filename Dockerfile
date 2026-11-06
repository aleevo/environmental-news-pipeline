
# 1. Start with an official lightweight Python image
FROM python:3.12-slim

# 2. Prevent Python from creating unnecessary cache files
ENV PYTHONDONTWRITEBYTECODE=1

# 3. Display Python logs immediately
ENV PYTHONUNBUFFERED=1

# 4. Set the working directory inside the container
WORKDIR /app

# 5. Copy dependency list into the container
COPY requirements.txt .

# 6. Install all Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 7. Copy the ingestion application
COPY ingestion/ ./ingestion/

# 8. Execute the RSS ingestion script
CMD ["python", "-u", "ingestion/ingest_rss.py"]
