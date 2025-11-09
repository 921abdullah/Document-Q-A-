import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Request
from app.db import SessionLocal, init_db
from app.models import Document
from app.core.logger import logger
from app.core.config import settings
from app.core.limiter import limiter
# from app.services.retrieval import update_indexes  # later when ready

router = APIRouter()
init_db()

DATA_DIR = "data/docs"
os.makedirs(DATA_DIR, exist_ok=True)
ALLOWED_EXTS = [".txt", ".md"]

@router.post("/")
@limiter.limit(f"{settings.RATE_LIMIT_INGEST_PER_MINUTE}/minute")
async def ingest_file(
    request: Request,
    file: UploadFile = File(None), 
    text: str = Form(None)
):
    db = SessionLocal()
    try:
        if file:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ALLOWED_EXTS:
                raise HTTPException(status_code=400, detail="Only .txt or .md files allowed.")
            content = (await file.read()).decode("utf-8")
            name = file.filename
        elif text:
            content = text
            name = f"manual_input_{len(text)}.txt"
        else:
            raise HTTPException(status_code=400, detail="No input provided.")

        # Check for duplicate doccs
        existing = db.query(Document).filter(Document.name == name).first()
        if existing:
            return {"message": f"Document '{name}' already exists.", "id": existing.id}

        # Save to disk
        with open(os.path.join(DATA_DIR, name), "w", encoding="utf-8") as f:
            f.write(content)

        # Save to DB
        doc = Document(name=name, content=content)
        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"Document {name} ingested successfully.")
        # update_indexes()  # (optional, after implementing retrieval)
        return {"id": doc.id, "name": doc.name, "message": "Document stored successfully."}

    finally:
        db.close()


@router.get("/list")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def list_documents(request: Request, skip: int = 0, limit: int = 10):
    db = SessionLocal()
    try:
        docs = db.query(Document).offset(skip).limit(limit).all()
        return [
            {"id": d.id, "name": d.name, "created_at": getattr(d, "created_at", None)}
            for d in docs
        ]
    finally:
        db.close()
