from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health():
    with patch("main.is_healthy", return_value=True):
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["qdrant"] == "connected"


def test_list_documents_empty():
    with patch("main.list_documents_with_counts", return_value=[]):
        response = client.get("/docs/list")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_rejects_non_pdf():
    response = client.post(
        "/docs/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


@patch("main.upload_pdf")
def test_upload_pdf_success(mock_upload):
    mock_upload.return_value = {
        "id": "abc123",
        "filename": "api-limits.pdf",
        "uploaded_at": "2026-07-06T00:00:00+00:00",
        "chunk_count": 3,
    }
    response = client.post(
        "/docs/upload",
        files={"file": ("api-limits.pdf", b"%PDF-1.4 fake", "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document"]["filename"] == "api-limits.pdf"
    assert body["document"]["chunk_count"] == 3
