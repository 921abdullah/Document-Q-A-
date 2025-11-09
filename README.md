# Document Q&A Microservice

A FastAPI-based Retrieval-Augmented Generation (RAG) microservice that enables question-answering over ingested documents using vector search and semantic retrieval.

## Features

- **Document Ingestion**: Upload text files (`.txt`, `.md`) or submit text directly via API
- **Semantic Search**: Multiple search modes including baseline (TF-IDF), vector (FAISS), and hybrid approaches
- **Question Answering**: Extract answers from ingested documents using transformer models
- **Vector Search**: FAISS-based vector similarity search with sentence transformers
- **Reranking**: Cross-encoder reranking for improved result quality
- **Rate Limiting**: IP-based rate limiting to protect API endpoints
- **Caching**: In-memory caching for improved performance
- **Health Monitoring**: Health check and metrics endpoints

## Architecture

### Technology Stack

- **Framework**: FastAPI
- **ML Models**: 
  - Sentence Transformers (for embeddings)
  - Cross-Encoder (for reranking)
- **Vector Database**: FAISS (Facebook AI Similarity Search)
- **Database**: SQLite (via SQLAlchemy)
- **Search Methods**: TF-IDF (baseline) and Vector similarity
- **Rate Limiting**: slowapi

### Search Modes

1. **Baseline**: TF-IDF-based keyword search
2. **Vector**: Semantic search using FAISS vector index
3. **Hybrid**: Combination of both approaches

## Prerequisites

- Python 3.11+
- pip
- (Optional) Docker and Docker Compose

## Installation

### Local Installation

1. **Clone the repository** (if applicable):
   ```bash
   git clone <repository-url>
   cd Document-Q-A-
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional):
   Create a `.env` file in the root directory:
   ```env
   DB_PATH=data/documents.db
   EMBED_MODEL=all-MiniLM-L6-v2
   CHUNK_SIZE=400
   RATE_LIMIT_PER_MINUTE=100
   RATE_LIMIT_QUERY_PER_MINUTE=30
   RATE_LIMIT_INGEST_PER_MINUTE=10
   ```

5. **Run the application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The API will be available at `http://localhost:8000`

### Docker Installation

1. **Build the Docker image**:
   ```bash
   docker build -t document-qa-app .
   ```

2. **Run the container**:
   ```bash
   docker run -p 8000:8000 \
     -v $(pwd)/data:/app/data \
     document-qa-app
   ```

   On Windows PowerShell:
   ```powershell
   docker run -p 8000:8000 -v ${PWD}/data:/app/data document-qa-app
   ```

3. **Access the API**:
   - API: `http://localhost:8000`
   - Interactive docs: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Configuration

Configuration can be set via environment variables or defaults will be used:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_PATH` | `data/documents.db` | SQLite database path |
| `EMBED_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model for embeddings |
| `CHUNK_SIZE` | `400` | Document chunk size for processing |
| `RATE_LIMIT_PER_MINUTE` | `100` | General rate limit per IP |
| `RATE_LIMIT_QUERY_PER_MINUTE` | `30` | Query endpoint rate limit |
| `RATE_LIMIT_INGEST_PER_MINUTE` | `10` | Ingest endpoint rate limit |

## API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. Root
- **GET** `/`
- **Description**: Welcome message
- **Rate Limit**: 100 requests/minute

**Response**:
```json
{
  "message": "Welcome to the Document Q&A microservice"
}
```

#### 2. Health Check
- **GET** `/meta/health`
- **Description**: Check service health
- **Rate Limit**: None

**Response**:
```json
{
  "status": "ok"
}
```

#### 3. Metrics
- **GET** `/meta/metrics`
- **Description**: Get service metrics
- **Rate Limit**: None

**Response**:
```json
{
  "uptime": "123.45s",
  "queries_processed": 0
}
```

#### 4. Ingest Document
- **POST** `/ingest/`
- **Description**: Upload a document or submit text
- **Rate Limit**: 10 requests/minute

**Request Options**:

**Option 1: File Upload**
```bash
curl -X POST "http://localhost:8000/ingest/" \
  -F "file=@document.txt"
```

**Option 2: Text Submission**
```bash
curl -X POST "http://localhost:8000/ingest/" \
  -F "text=Your document content here"
```

**Response**:
```json
{
  "id": 1,
  "name": "document.txt",
  "message": "Document stored successfully."
}
```

#### 5. List Documents
- **GET** `/ingest/list?skip=0&limit=10`
- **Description**: List ingested documents
- **Rate Limit**: 100 requests/minute
- **Query Parameters**:
  - `skip` (int): Number of documents to skip (default: 0)
  - `limit` (int): Maximum number of documents to return (default: 10)

**Response**:
```json
[
  {
    "id": 1,
    "name": "document.txt",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

#### 6. Query Documents
- **POST** `/query/`
- **Description**: Ask questions about ingested documents
- **Rate Limit**: 30 requests/minute

**Request Body**:
```json
{
  "query": "What is mitochondria?",
  "mode": "baseline"
}
```

**Parameters**:
- `query` (string, required): The question to ask
- `mode` (string, optional): Search mode - `baseline`, `vector`, or `hybrid` (default: `baseline`)

**Response**:
```json
{
  "answer": "Mitochondria are the powerhouse of the cell...",
  "sources": [
    {
      "name": "biology.txt",
      "content": "Mitochondria are organelles...",
      "score": 0.95
    }
  ]
}
```

## Usage Examples

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Ingest a document
with open("document.txt", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/ingest/",
        files={"file": ("document.txt", f, "text/plain")}
    )
    print(response.json())

# 2. Query the documents
response = requests.post(
    f"{BASE_URL}/query/",
    json={
        "query": "What is the main topic?",
        "mode": "vector"
    }
)
result = response.json()
print(f"Answer: {result['answer']}")
print(f"Sources: {len(result['sources'])} documents found")
```

### cURL Examples

**Ingest a document**:
```bash
curl -X POST "http://localhost:8000/ingest/" \
  -F "text=The mitochondria is the powerhouse of the cell."
```

**Query documents**:
```bash
curl -X POST "http://localhost:8000/query/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is mitochondria?",
    "mode": "baseline"
  }'
```

**List documents**:
```bash
curl "http://localhost:8000/ingest/list?limit=5"
```

## Testing

Run tests using pytest:

```bash
pytest tests/
```

Run with verbose output:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_query.py
```

## Rate Limiting

The API implements IP-based rate limiting to prevent abuse:

- **General endpoints**: 100 requests/minute
- **Query endpoint**: 30 requests/minute
- **Ingest endpoint**: 10 requests/minute

When rate limits are exceeded, the API returns:
- **Status Code**: `429 Too Many Requests`
- **Response**: Includes retry information

Rate limits can be configured via environment variables (see Configuration section).

## Project Structure

```
Document-Q-A-
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── ingest.py          # Document ingestion endpoints
│   │   ├── query.py           # Query endpoints
│   │   └── meta.py            # Health and metrics endpoints
│   ├── core/
│   │   ├── config.py          # Configuration settings
│   │   ├── limiter.py         # Rate limiting setup
│   │   └── logger.py          # Logging configuration
│   ├── services/
│   │   ├── answering.py       # Answer extraction logic
│   │   ├── retrieval.py       # Search and retrieval logic
│   │   └── storage.py         # Document storage utilities
│   ├── models.py              # Database models
│   ├── db.py                  # Database configuration
│   └── main.py                # FastAPI application entry point
├── data/
│   ├── docs/                  # Stored documents
│   ├── documents.db           # SQLite database
│   ├── embeddings.npy         # Document embeddings
│   └── vector_index.faiss    # FAISS vector index
├── tests/
│   ├── conftest.py
│   └── test_query.py          # API tests
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## How It Works

1. **Document Ingestion**:
   - Documents are uploaded via the `/ingest/` endpoint
   - Content is stored in SQLite database and on disk
   - Documents are chunked and processed for search

2. **Vector Index Building**:
   - On startup, the service builds a FAISS vector index
   - Documents are embedded using sentence transformers
   - Index is saved for faster subsequent queries

3. **Query Processing**:
   - User submits a query via `/query/` endpoint
   - Query is processed using selected search mode:
     - **Baseline**: TF-IDF keyword matching
     - **Vector**: Semantic similarity search using FAISS
     - **Hybrid**: Combination of both methods
   - Results are reranked using cross-encoder
   - Answer is extracted from top-ranked documents

## Development

### Running in Development Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reload on code changes.

### Code Style

The project follows PEP 8 Python style guidelines. Consider using:
- `black` for code formatting
- `flake8` or `pylint` for linting

## Notes

- **First Run**: The first query may take longer as models are downloaded and loaded
- **Memory Usage**: ML models require significant RAM (recommended: 4GB+)
- **Storage**: Vector indexes and embeddings are stored in the `data/` directory
- **Database**: SQLite database is created automatically on first run

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[Add your license here]

## Support

For issues and questions, please open an issue on the repository.

---

**Built with FastAPI, Sentence Transformers, and FAISS**
