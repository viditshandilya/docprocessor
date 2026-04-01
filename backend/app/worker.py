import time
import json
import os
import redis
import random
from celery import Celery
from app.database import SessionLocal
from app.services.document_service import update_document_status, update_document_result

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")

celery_app = Celery("worker", broker=CELERY_BROKER_URL)
redis_client = redis.from_url(REDIS_URL)


def publish_progress(doc_id: str, stage: str, progress: int, status: str):
    event = {
        "doc_id": doc_id,
        "stage": stage,
        "progress": progress,
        "status": status
    }

    # Send to frontend via Redis Pub/Sub
    redis_client.publish(f"progress:{doc_id}", json.dumps(event))

    # Update DB
    db = SessionLocal()
    try:
        update_document_status(db, doc_id, status, progress, stage)
    finally:
        db.close()


@celery_app.task(name="process_document")
def process_document(doc_id: str, filename: str, file_type: str, file_size: int):
    db = SessionLocal()

    try:
        # 🔴 Simulate random failure (20%)
        if random.random() < 0.2:
            publish_progress(doc_id, "job_failed", 0, "failed")
            return

        # Stage 1: job started
        publish_progress(doc_id, "job_started", 10, "processing")
        time.sleep(1)

        # Stage 2: parsing started
        publish_progress(doc_id, "document_parsing_started", 25, "processing")
        time.sleep(2)

        # Stage 3: parsing completed
        publish_progress(doc_id, "document_parsing_completed", 40, "processing")
        time.sleep(1)

        # Stage 4: extraction started
        publish_progress(doc_id, "field_extraction_started", 55, "processing")
        time.sleep(2)

        # Stage 5: extraction completed
        publish_progress(doc_id, "field_extraction_completed", 75, "processing")
        time.sleep(1)

        # Stage 6: generate fake result
        name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ").title()

        result = {
            "title": name,
            "filename": filename,
            "file_type": file_type,
            "file_size": f"{round(file_size / 1024, 2)} KB",
            "category": "General",
            "summary": f"This document '{name}' has been processed successfully. It is a {file_type} file.",
            "keywords": [
                name.split()[0] if name.split() else "doc",
                file_type,
                "uploaded",
                "processed"
            ],
            "status": "completed"
        }

        # Stage 7: store result
        publish_progress(doc_id, "final_result_stored", 90, "processing")
        time.sleep(1)

        update_document_result(db, doc_id, result)

        # Stage 8: completed
        publish_progress(doc_id, "job_completed", 100, "completed")

    except Exception as e:
        publish_progress(doc_id, "job_failed", 0, "failed")
        raise e

    finally:
        db.close()