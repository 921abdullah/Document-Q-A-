import os
from app.db import SessionLocal
from app.models import Document
from app.core.logger import logger

DATA_DIR = "data/docs"
os.makedirs(DATA_DIR, exist_ok=True)

def save_document(name: str, content: str):
    """Save content both in DB and as a file."""
    file_path = os.path.join(DATA_DIR, name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    db = SessionLocal()
    doc = Document(name=name, content=content)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    db.close()

    logger.info(f"Document {name} stored successfully.")
    return doc

