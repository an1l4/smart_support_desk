"""Seed the billing tables with sample data."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.billing_lookup import seed_billing_data  # noqa: E402


def main() -> None:
    seed_billing_data()
    print("Billing tables seeded (accounts + invoices).")


if __name__ == "__main__":
    main()

