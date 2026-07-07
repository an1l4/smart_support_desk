import sqlite3

from config import TICKETS_DB


ACCOUNTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS billing_accounts (
    email TEXT PRIMARY KEY,
    plan TEXT NOT NULL,
    balance_due REAL NOT NULL,
    last_payment TEXT
);
"""

INVOICES_SCHEMA = """
CREATE TABLE IF NOT EXISTS billing_invoices (
    id TEXT PRIMARY KEY,
    email TEXT NOT NULL,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (email) REFERENCES billing_accounts (email)
);
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(TICKETS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _connect() as conn:
        conn.execute(ACCOUNTS_SCHEMA)
        conn.execute(INVOICES_SCHEMA)
        conn.commit()


def seed_billing_data() -> None:
    """Seed the billing tables with sample data (idempotent)."""
    _init_db()
    sample_accounts = [
        {"email": "alice@example.com", "plan": "pro", "balance_due": 0.0, "last_payment": "2026-06-01"},
        {"email": "bob@example.com", "plan": "free", "balance_due": 0.0, "last_payment": None},
        {"email": "carol@example.com", "plan": "pro", "balance_due": 29.99, "last_payment": "2026-05-01"},
        {"email": "dave@example.com", "plan": "enterprise", "balance_due": 0.0, "last_payment": "2026-06-10"},
        {"email": "eve@example.com", "plan": "pro", "balance_due": 0.0, "last_payment": "2026-06-05"},
        {"email": "frank@example.com", "plan": "free", "balance_due": 0.0, "last_payment": None},
        {"email": "grace@example.com", "plan": "pro", "balance_due": 59.98, "last_payment": "2026-04-01"},
        {"email": "henry@example.com", "plan": "enterprise", "balance_due": 0.0, "last_payment": "2026-06-20"},
        {"email": "iris@example.com", "plan": "pro", "balance_due": 0.0, "last_payment": "2026-06-12"},
        {"email": "jack@example.com", "plan": "free", "balance_due": 0.0, "last_payment": None},
    ]
    sample_invoices = [
        {"id": "INV-101", "email": "alice@example.com", "date": "2026-06-01", "amount": 29.99, "status": "paid", "description": "Pro plan - June 2026"},
        {"id": "INV-102", "email": "alice@example.com", "date": "2026-06-15", "amount": 29.99, "status": "pending_review", "description": "Pro plan - duplicate charge under review"},
        {"id": "INV-201", "email": "carol@example.com", "date": "2026-06-01", "amount": 29.99, "status": "unpaid", "description": "Pro plan - June 2026"},
        {"id": "INV-301", "email": "dave@example.com", "date": "2026-06-10", "amount": 499.00, "status": "paid", "description": "Enterprise plan - June 2026"},
        {"id": "INV-401", "email": "eve@example.com", "date": "2026-06-05", "amount": 29.99, "status": "paid", "description": "Pro plan - June 2026"},
        {"id": "INV-501", "email": "grace@example.com", "date": "2026-05-01", "amount": 29.99, "status": "paid", "description": "Pro plan - May 2026"},
        {"id": "INV-502", "email": "grace@example.com", "date": "2026-06-01", "amount": 29.99, "status": "unpaid", "description": "Pro plan - June 2026"},
        {"id": "INV-601", "email": "henry@example.com", "date": "2026-06-20", "amount": 499.00, "status": "paid", "description": "Enterprise plan - June 2026"},
        {"id": "INV-701", "email": "iris@example.com", "date": "2026-06-12", "amount": 29.99, "status": "paid", "description": "Pro plan - June 2026"},
    ]

    with _connect() as conn:
        for acc in sample_accounts:
            conn.execute(
                """
                INSERT OR IGNORE INTO billing_accounts (email, plan, balance_due, last_payment)
                VALUES (?, ?, ?, ?)
                """,
                (
                    acc["email"],
                    acc["plan"],
                    acc["balance_due"],
                    acc["last_payment"],
                ),
            )

        for inv in sample_invoices:
            conn.execute(
                """
                INSERT OR IGNORE INTO billing_invoices (id, email, date, amount, status, description)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    inv["id"],
                    inv["email"],
                    inv["date"],
                    inv["amount"],
                    inv["status"],
                    inv["description"],
                ),
            )
        conn.commit()


def get_account_by_email(email: str) -> dict | None:
    """Look up customer billing record from the billing_accounts table."""
    _init_db()
    email_lower = email.strip().lower()
    with _connect() as conn:
        account_row = conn.execute(
            "SELECT email, plan, balance_due, last_payment FROM billing_accounts WHERE LOWER(email) = ?",
            (email_lower,),
        ).fetchone()
        if account_row is None:
            return None

        invoice_rows = conn.execute(
            """
            SELECT id, date, amount, status, description
            FROM billing_invoices
            WHERE email = ?
            ORDER BY date
            """,
            (account_row["email"],),
        ).fetchall()

    invoices = [
        {
            "id": row["id"],
            "date": row["date"],
            "amount": row["amount"],
            "status": row["status"],
            "description": row["description"],
        }
        for row in invoice_rows
    ]

    return {
        "email": account_row["email"],
        "plan": account_row["plan"],
        "balance_due": account_row["balance_due"],
        "last_payment": account_row["last_payment"],
        "invoices": invoices,
    }


def explain_invoice(email: str, invoice_id: str) -> str:
    """Return human-readable invoice explanation from the billing_invoices table."""
    _init_db()
    email_lower = email.strip().lower()
    invoice_id_upper = invoice_id.strip().upper()

    with _connect() as conn:
        account_row = conn.execute(
            "SELECT email FROM billing_accounts WHERE LOWER(email) = ?",
            (email_lower,),
        ).fetchone()
        if account_row is None:
            return f"No account found for {email}."

        invoice_row = conn.execute(
            """
            SELECT id, date, amount, status, description
            FROM billing_invoices
            WHERE email = ? AND UPPER(id) = ?
            """,
            (account_row["email"], invoice_id_upper),
        ).fetchone()

        if invoice_row is None:
            ids_rows = conn.execute(
                "SELECT id FROM billing_invoices WHERE email = ?",
                (account_row["email"],),
            ).fetchall()
            ids = ", ".join(r["id"] for r in ids_rows) or "none"
            return f"Invoice {invoice_id} not found for {email}. Available invoices: {ids}."

    return (
        f"Invoice {invoice_row['id']} ({invoice_row['date']}): "
        f"${invoice_row['amount']:.2f} — {invoice_row['description'] or 'No description'}. "
        f"Status: {invoice_row['status']}."
    )
