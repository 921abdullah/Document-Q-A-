from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.db import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
