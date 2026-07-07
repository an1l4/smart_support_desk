import sqlite3
from datetime import datetime, timezone

from config import TICKETS_DB

_SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    chunk_count INTEGER NOT NULL DEFAULT 0
)
"""


def _connect() -> sqlite3.Connection:
    TICKETS_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(TICKETS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _connect() as conn:
        conn.execute(_SCHEMA)
        conn.commit()


def add_document(*, doc_id: str, filename: str, chunk_count: int) -> dict:
    _init_db()
    uploaded_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO documents (id, filename, uploaded_at, chunk_count)
            VALUES (?, ?, ?, ?)
            """,
            (doc_id, filename, uploaded_at, chunk_count),
        )
        conn.commit()
    return {
        "id": doc_id,
        "filename": filename,
        "uploaded_at": uploaded_at,
        "chunk_count": chunk_count,
    }


def list_documents() -> list[dict]:
    _init_db()
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, filename, uploaded_at, chunk_count FROM documents ORDER BY uploaded_at"
        ).fetchall()
    return [dict(row) for row in rows]


def get_document(doc_id: str) -> dict | None:
    _init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, filename, uploaded_at, chunk_count FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
    return dict(row) if row else None


def update_chunk_count(doc_id: str, chunk_count: int) -> None:
    _init_db()
    with _connect() as conn:
        conn.execute(
            "UPDATE documents SET chunk_count = ? WHERE id = ?",
            (chunk_count, doc_id),
        )
        conn.commit()


def delete_document(doc_id: str) -> bool:
    _init_db()
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    return cursor.rowcount > 0


def filename_exists(filename: str) -> bool:
    _init_db()
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM documents WHERE filename = ?",
            (filename,),
        ).fetchone()
    return row is not None
