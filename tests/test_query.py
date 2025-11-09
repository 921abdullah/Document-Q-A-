from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_ingest_and_query():
    # Ingest a sample doc
    text = "The mitochondria is the powerhouse of the cell."
    resp = client.post("/ingest/", data={"text": text})
    assert resp.status_code == 200

    # Query for it
    q = {"query": "What is mitochondria?", "mode": "baseline"}
    resp = client.post("/query/", json=q)
    assert resp.status_code == 200
    data = resp.json()
    assert "mitochondria" in data["answer"].lower()

def test_ingest_file_upload(tmp_path):
    """
    Test ingestion using an uploaded text file instead of raw form text.
    """
    # Create a temporary text file
    file_path = tmp_path / "sample1.txt"
    file_path.write_text("Lipids are a broad group of organic compounds which include fats, waxes, sterols, fat-soluble vitamins, monoglycerides, diglycerides, phospholipids, and others.")

    # Upload file to /ingest/
    with open(file_path, "rb") as f:
        resp = client.post("/ingest/", files={"file": ("sample.txt", f, "text/plain")})

    # Check response
    assert resp.status_code == 200
    data = resp.json()
    assert "stored successfully" in data["message"].lower()

    # Verify the document is now listed
    list_resp = client.get("/ingest/list")
    assert list_resp.status_code == 200
    docs = list_resp.json()
    assert any("sample.txt" in d["name"] for d in docs)



