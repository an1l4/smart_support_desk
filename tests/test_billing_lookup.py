import sqlite3

import pytest

from config import TICKETS_DB
from tools.billing_lookup import explain_invoice, get_account_by_email, seed_billing_data


@pytest.fixture(autouse=True)
def fresh_billing_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr("tools.billing_lookup.TICKETS_DB", db_path)
    seed_billing_data()
    yield


def test_get_account_by_email_found():
    account = get_account_by_email("alice@example.com")
    assert account is not None
    assert account["plan"] == "pro"
    assert len(account["invoices"]) == 2


def test_get_account_by_email_not_found():
    assert get_account_by_email("unknown@example.com") is None


def test_explain_invoice_found():
    result = explain_invoice("alice@example.com", "INV-102")
    assert "INV-102" in result
    assert "pending_review" in result


def test_seed_is_idempotent():
    seed_billing_data()
    seed_billing_data()
    with sqlite3.connect(TICKETS_DB) as conn:
        count = conn.execute("SELECT COUNT(*) FROM billing_accounts").fetchone()[0]
    assert count == 10
