from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.services.retrieval import load_vector_index
from app.api import ingest, query, meta
from app.core.logger import logger
from app.core.config import settings
from app.core.limiter import limiter

@asynccontextmanager
async def lifespan(app: FastAPI):
    #Runs once at startup
    logger.info("Starting up... Initializing cache.")
    FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    load_vector_index()
    yield  

    #Runs once at shutdown
    logger.info("Shutting down... cleaning up resources.")

# Create FastAPI app with lifespan
app = FastAPI(title="RAG Microservice", version="1.0", lifespan=lifespan)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Routers
app.include_router(ingest.router, prefix="/ingest", tags=["Ingestion"])
app.include_router(query.router, prefix="/query", tags=["Query"])
app.include_router(meta.router, tags=["Meta"])

@app.get("/")
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
def root(request: Request):
    return {"message": "Welcome to the Document Q&A microservice"}

