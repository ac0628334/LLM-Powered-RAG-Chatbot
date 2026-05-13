import os
from celery import Celery
from dotenv import load_dotenv
from src.ingest import ingest_uploaded_file

# Load environment variables
load_dotenv()

# Configure Celery with Redis broker
celery_app = Celery(
    "worker",
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")
)

@celery_app.task
def ingest_file_task(filename: str, data: bytes, data_dir: str):
    """
    Celery task to ingest a file asynchronously.
    """
    return ingest_uploaded_file(filename, data, data_dir)
