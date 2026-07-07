import json
import sqlite3
import uuid
from datetime import datetime, timezone

from config import TICKETS_DB

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    category TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    subject TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    resolution TEXT,
    metadata TEXT,
    created_at TEXT NOT NULL
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


def create_ticket(
    *,
    category: str,
    customer_email: str,
    subject: str,
    message: str,
    severity: str | None = None,
    status: str = "open",
    resolution: str | None = None,
    metadata: dict | None = None,
) -> str:
    _init_db()
    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    created_at = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO tickets (
                id, category, customer_email, subject, message,
                severity, status, resolution, metadata, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ticket_id,
                category,
                customer_email,
                subject,
                message,
                severity,
                status,
                resolution,
                json.dumps(metadata or {}),
                created_at,
            ),
        )
        conn.commit()
    return ticket_id


def update_ticket(ticket_id: str, **fields) -> None:
    if not fields:
        return
    _init_db()
    allowed = {"severity", "status", "resolution", "metadata"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    if "metadata" in updates and isinstance(updates["metadata"], dict):
        updates["metadata"] = json.dumps(updates["metadata"])
    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [ticket_id]
    with _connect() as conn:
        conn.execute(f"UPDATE tickets SET {set_clause} WHERE id = ?", values)
        conn.commit()


def get_ticket(ticket_id: str) -> dict | None:
    _init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["metadata"] = json.loads(data["metadata"] or "{}")
    return data
