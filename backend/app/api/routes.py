import os
import csv
import json
import uuid
import aiofiles
import redis
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.document_service import (
    create_document, get_document, get_all_documents,
    finalize_document, retry_document
)
from app.worker import process_document
import io

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL)

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_documents(files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    uploaded = []
    for file in files:
        content = await file.read()
        file_size = len(content)
        file_type = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "unknown"
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        doc = create_document(db, file.filename, file_type, file_size)
        process_document.delay(doc.id, doc.filename, doc.file_type, doc.file_size)
        uploaded.append({"id": doc.id, "filename": doc.filename, "status": doc.status})
    return {"uploaded": uploaded}

@router.get("/documents")
def list_documents(status: str = None, search: str = None, sort: str = "created_at", db: Session = Depends(get_db)):
    docs = get_all_documents(db, status=status, search=search, sort=sort)
    return {"documents": [doc_to_dict(d) for d in docs]}

@router.get("/documents/{doc_id}")
def get_document_detail(doc_id: str, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_to_dict(doc)

@router.get("/documents/{doc_id}/progress")
def get_progress(doc_id: str, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": doc.status, "progress": doc.progress, "stage": doc.current_stage}

@router.get("/documents/{doc_id}/stream")
def stream_progress(doc_id: str):
    def event_stream():
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"progress:{doc_id}")
        for message in pubsub.listen():
            if message["type"] == "message":
                data = message["data"].decode("utf-8")
                yield f"data: {data}\n\n"
                parsed = json.loads(data)
                if parsed.get("status") in ["completed", "failed"]:
                    break
    return StreamingResponse(event_stream(), media_type="text/event-stream")

@router.post("/documents/{doc_id}/retry")
def retry_failed(doc_id: str, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "failed":
        raise HTTPException(status_code=400, detail="Only failed jobs can be retried")
    doc = retry_document(db, doc_id)
    process_document.delay(doc.id, doc.filename, doc.file_type, doc.file_size)
    return {"message": "Retry started", "id": doc.id}

@router.put("/documents/{doc_id}/finalize")
def finalize(doc_id: str, body: dict, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = finalize_document(db, doc_id, body)
    return {"message": "Finalized", "id": doc.id}

@router.get("/documents/{doc_id}/export/json")
def export_json(doc_id: str, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    if not doc or not doc.result:
        raise HTTPException(status_code=404, detail="No result found")
    return JSONResponse(content=doc.result)

@router.get("/documents/{doc_id}/export/csv")
def export_csv(doc_id: str, db: Session = Depends(get_db)):
    doc = get_document(db, doc_id)
    if not doc or not doc.result:
        raise HTTPException(status_code=404, detail="No result found")
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=doc.result.keys())
    writer.writeheader()
    writer.writerow({k: ", ".join(v) if isinstance(v, list) else v for k, v in doc.result.items()})
    output.seek(0)
    return StreamingResponse(output, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={doc_id}.csv"})

def doc_to_dict(doc):
    return {
        "id": doc.id,
        "filename": doc.filename,
        "file_type": doc.file_type,
        "file_size": doc.file_size,
        "status": doc.status,
        "progress": doc.progress,
        "current_stage": doc.current_stage,
        "result": doc.result,
        "finalized": doc.finalized,
        "retry_count": doc.retry_count,
        "created_at": str(doc.created_at) if doc.created_at else None,
    }