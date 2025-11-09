from fastapi import APIRouter, Body, Request
from app.services.retrieval import search, rerank_results
from app.services.answering import extractive_answer
from app.core.config import settings
from app.core.limiter import limiter

router = APIRouter()

@router.post("/")
@limiter.limit(f"{settings.RATE_LIMIT_QUERY_PER_MINUTE}/minute")
def query_documents(
    request: Request,
    query: str = Body(..., embed=True),
    mode: str = Body("baseline", embed=True),
):

    results = search(query, mode)
    if not results:
        return {"answer": "Sorry, I do not have relevant information. :(", "sources": []}

    results = rerank_results(query, results)
    answer = extractive_answer(query, results)
    return {"answer": answer, "sources": results}
