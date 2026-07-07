"""Upload all sample PDFs from data/sample_pdfs/ into the knowledge base."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import SAMPLE_PDFS_DIR
from tools.doc_search import list_documents_with_counts, upload_pdf


def seed_sample_pdfs(directory: Path | None = None) -> list[dict]:
    source = directory or SAMPLE_PDFS_DIR
    if not source.exists():
        raise FileNotFoundError(
            f"Sample PDF directory not found: {source}. "
            "Run: python scripts/generate_sample_pdfs.py"
        )

    existing = {doc["filename"] for doc in list_documents_with_counts()}
    uploaded: list[dict] = []

    for pdf_path in sorted(source.glob("*.pdf")):
        if pdf_path.name in existing:
            print(f"Skip (already uploaded): {pdf_path.name}")
            continue
        content = pdf_path.read_bytes()
        doc = upload_pdf(content, pdf_path.name)
        uploaded.append(doc)
        print(f"Uploaded: {pdf_path.name} ({doc['chunk_count']} chunks)")

    return uploaded


if __name__ == "__main__":
    docs = seed_sample_pdfs()
    print(f"\nDone. {len(docs)} new PDF(s) indexed.")
