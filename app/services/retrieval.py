# app/services/retrieval.py

from sentence_transformers import SentenceTransformer, CrossEncoder
import faiss
import numpy as np
import os
from app.db import SessionLocal
from app.models import Document
from app.core.logger import logger
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import CrossEncoder
from functools import lru_cache
from app.core.logger import logger
from dotenv import load_dotenv
import transformers
import re
transformers.utils.logging.set_verbosity_error()

# logger.info(f"Index built successfully with {len(docs)} documents.")
# logger.warning(f"Low confidence score for query: '{query}'")
# logger.error("Failed to load FAISS index.", exc_info=True)


load_dotenv()

FAISS_PATH = os.getenv("FAISS_PATH", "data/vector_index.faiss")
EMB_PATH = os.getenv("EMB_PATH", "data/embeddings.npy")
embedder = os.getenv("EMBEDDER", "all-MiniLM-L6-v2")
reranker = os.getenv("RERANKER", "cross-encoder/ms-marco-MiniLM-L-6-v2")
BASELINE_THRESHOLD = float(os.getenv("BASELINE_THRESH", 0.15))
VECTOR_THRESHOLD = float(os.getenv("VECTOR_THRESH", 0.55))
HYBRID_THRESHOLD = float(os.getenv("HYBRID_THRESH", 0.50))

# ----------------------------- #
# Globals
# ----------------------------- #

tfidf_vectorizer = None
tfidf_matrix = None
vector_index = None
docs_cache = []

@lru_cache(maxsize=1)
def get_embedder():
    logger.info(f"Loading embedder model: {embedder}")
    return SentenceTransformer(embedder)

@lru_cache(maxsize=1)
def get_reranker():
    logger.info(f"Loading reranker model: {reranker}")
    return CrossEncoder(reranker)


def safe_snippet(text: str, limit: int = 800) -> str:
    """
    Returns a clean snippet ending at a sentence boundary.
    - limit: max number of characters before truncating
    - ensures no abrupt cut mid-sentence
    """
    text = text.strip().replace("\n", " ")
    if len(text) <= limit:
        return text

    # take only up to limit characters
    snippet = text[:limit]

    # find nearest sentence-ending punctuation before cutoff
    end_idx = max(snippet.rfind("."), snippet.rfind("?"), snippet.rfind("!"))
    if end_idx != -1 and end_idx > limit * 0.4:  # ensure it’s not too early
        snippet = snippet[:end_idx + 1]
    else:
        snippet = snippet + "..."  # fallback if no punctuation found

    return snippet

def rerank_results(query: str, results: list):
    """
    Re-ranks top-k retrieved results using a cross-encoder model.
    """
    if not results:
        return results

    # Prepare pairs for cross-encoder
    pairs = [(query, r["snippet"]) for r in results]
    reranker = get_reranker()
    scores = reranker.predict(pairs)

    # Attach scores and sort
    for i, r in enumerate(results):
        r["rerank_score"] = float(scores[i])

    results.sort(key=lambda x: x["rerank_score"], reverse=True)
    return results

# ----------------------------- #
# Baseline (TF-IDF)
# ----------------------------- #
def build_tfidf_index():
    global tfidf_vectorizer, tfidf_matrix, docs_cache
    db = SessionLocal()
    docs = db.query(Document).all()
    db.close()

    if not docs:
        logger.warning("No documents found for TF-IDF index.")
        return

    docs_cache = [(d.id, d.name, d.content) for d in docs]
    contents = [d.content for d in docs]

    tfidf_vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = tfidf_vectorizer.fit_transform(contents)
    logger.info(f"TF-IDF index built for {len(docs)} documents.")

def search_baseline(query: str, top_k: int = 3):
    global tfidf_vectorizer, tfidf_matrix, docs_cache
    if tfidf_vectorizer is None or tfidf_matrix is None:
        build_tfidf_index()

    query_vec = tfidf_vectorizer.transform([query])
    sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
    top_idx = np.argsort(sims)[::-1][:top_k]

    results = []
    for i in top_idx:
        doc_id, name, content = docs_cache[i]
        results.append({
            "id": doc_id,
            "name": name,
            "score": float(sims[i]),
            # "snippet": content[:300].replace("\n", " ")
            "snippet": safe_snippet(content)

        })
    return results

# ----------------------------- #
# Vector (FAISS)
# ----------------------------- #
def build_vector_index():
    global vector_index, docs_cache
    db = SessionLocal()
    docs = db.query(Document).all()
    db.close()

    if not docs:
        logger.warning("No documents found for vector index.")
        return

    docs_cache = [(d.id, d.name, d.content) for d in docs]
    contents = [d.content for d in docs]

    embedder = get_embedder()
    embeddings = embedder.encode(contents, convert_to_numpy=True)
    dim = embeddings.shape[1]
    vector_index = faiss.IndexFlatL2(dim)
    vector_index.add(embeddings)

    os.makedirs("data", exist_ok=True)
    faiss.write_index(vector_index, FAISS_PATH)
    np.save(EMB_PATH, embeddings)
    logger.info(f"FAISS index built and saved for {len(docs)} documents.")

def load_vector_index():
    global vector_index, docs_cache
    if os.path.exists(FAISS_PATH):
        vector_index = faiss.read_index(FAISS_PATH)
        logger.info("Loaded FAISS index from disk.")
    else:
        build_vector_index()

def search_vector(query: str, top_k: int = 3):
    global vector_index, docs_cache
    if vector_index is None:
        load_vector_index()

    embedder = get_embedder()
    query_emb = embedder.encode([query], convert_to_numpy=True)
    D, I = vector_index.search(query_emb, top_k)

    results = []
    for rank, idx in enumerate(I[0]):
        if idx < len(docs_cache):
            doc_id, name, content = docs_cache[idx]
            results.append({
                "id": doc_id,
                "name": name,
                "score": float(D[0][rank]),
                # "snippet": content[:300].replace("\n", " ")
                "snippet": safe_snippet(content)
            })
    return results

# ----------------------------- #
# Hybrid (TF-IDF + FAISS)
# ----------------------------- #

def normalize_scores(vector_results):
    """Convert FAISS L2 distances into normalized 0-1 similarity scores."""
    if not vector_results:
        return []

    distances = np.array([r["score"] for r in vector_results], dtype=float)
    sims = 1 / (1 + distances)  # inverse distance
    sims = (sims - sims.min()) / (sims.max() - sims.min() + 1e-8)  # min–max normalize

    for i, r in enumerate(vector_results):
        r["score"] = float(sims[i])

    return vector_results

def search_hybrid(query: str, top_k: int = 3, alpha: float = 0.6):
    """
    Combine baseline (TF-IDF) and vector (FAISS) retrieval.
    alpha = weight for vector similarity.
    """
    baseline_results = search_baseline(query, top_k * 2)
    vector_results = search_vector(query, top_k * 2)
    vector_results = normalize_scores(vector_results)  # <-- new line

    # # Normalize vector distances into similarity scores (smaller → higher similarity)
    # max_score = max([r["score"] for r in vector_results]) if vector_results else 1
    # min_score = min([r["score"] for r in vector_results]) if vector_results else 0
    # for r in vector_results:
    #     r["score"] = 1 - (r["score"] - min_score) / (max_score - min_score + 1e-8)

    # Merge by document name
    combined = {}
    for r in baseline_results:
        combined[r["name"]] = {"snippet": r["snippet"], "baseline": r["score"], "vector": 0.0}
    for r in vector_results:
        if r["name"] not in combined:
            combined[r["name"]] = {"snippet": r["snippet"], "baseline": 0.0, "vector": r["score"]}
        else:
            combined[r["name"]]["vector"] = r["score"]

    # Weighted hybrid score
    merged = []
    for name, vals in combined.items():
        hybrid_score = alpha * vals["vector"] + (1 - alpha) * vals["baseline"]
        merged.append({
            "name": name,
            "snippet": vals["snippet"],
            "score": round(float(hybrid_score), 4)
        })

    # Sort and select top-k
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged[:top_k]


# ----------------------------- #
# Unified Interface
# ----------------------------- #
def search(query: str, mode: str = "baseline", top_k: int = 3):
    if mode == "vector":
        results = search_vector(query, top_k)
        threshold = VECTOR_THRESHOLD
    elif mode == "hybrid":
        results = search_hybrid(query, top_k)
        threshold = HYBRID_THRESHOLD
    else:
        results = search_baseline(query, top_k)
        threshold = BASELINE_THRESHOLD

    if not results:
        return []

    # Check top result’s score
    top_score = results[0]["score"]
    if top_score < threshold:
        logger.warning(f"Low confidence ({top_score:.3f}) for query: '{query}'")
        return []

    return results

