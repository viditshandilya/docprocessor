from sqlalchemy.orm import Session
from app.models.document import Document
import uuid

def create_document(db: Session, filename: str, file_type: str, file_size: int):
    doc = Document(
        id=str(uuid.uuid4()),
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        status="queued",
        progress=0,
        current_stage="job_queued"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document(db: Session, doc_id: str):
    return db.query(Document).filter(Document.id == doc_id).first()

def get_all_documents(db: Session, status: str = None, search: str = None, sort: str = "created_at"):
    query = db.query(Document)
    if status:
        query = query.filter(Document.status == status)
    if search:
        query = query.filter(Document.filename.ilike(f"%{search}%"))
    if sort == "created_at":
        query = query.order_by(Document.created_at.desc())
    elif sort == "filename":
        query = query.order_by(Document.filename.asc())
    elif sort == "status":
        query = query.order_by(Document.status.asc())
    return query.all()

def update_document_status(db: Session, doc_id: str, status: str, progress: int, stage: str):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = status
        doc.progress = progress
        doc.current_stage = stage
        db.commit()
        db.refresh(doc)
    return doc

def update_document_result(db: Session, doc_id: str, result: dict):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.result = result
        doc.status = "completed"
        doc.progress = 100
        doc.current_stage = "job_completed"
        db.commit()
        db.refresh(doc)
    return doc

def finalize_document(db: Session, doc_id: str, result: dict):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.result = result
        doc.finalized = 1
        db.commit()
        db.refresh(doc)
    return doc

def retry_document(db: Session, doc_id: str):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        doc.status = "queued"
        doc.progress = 0
        doc.current_stage = "job_queued"
        doc.retry_count += 1
        db.commit()
        db.refresh(doc)
    return doc