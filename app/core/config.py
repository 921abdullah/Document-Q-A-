import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DB_PATH: str = os.getenv("DB_PATH", "data/documents.db")
    EMBEDDING_MODEL: str = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", 400))
    # Rate limiting settings
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    RATE_LIMIT_QUERY_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_QUERY_PER_MINUTE", "30"))
    RATE_LIMIT_INGEST_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_INGEST_PER_MINUTE", "10"))

settings = Settings()

