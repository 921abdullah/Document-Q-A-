from fastapi import APIRouter
import time

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/metrics")
def metrics():
    return {
        "uptime": f"{time.perf_counter():.2f}s",
        "queries_processed": 0,  # add logic later
    }

