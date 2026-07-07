import re
import uuid
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from tools.doc_registry import add_document, delete_document as remove_doc_record, list_documents
from tools.embeddings import embed_texts_safe
from tools.vector_store import (
    count_chunks_for_doc,
    delete_chunks_by_doc_id,
    search_vectors,
    upsert_chunks,
)

CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


def _chunk_text(text: str, source: str, doc_id: str) -> list[dict]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
    chunks: list[dict] = []
    buffer = ""

    for paragraph in paragraphs:
        if len(buffer) + len(paragraph) + 2 <= CHUNK_SIZE:
            buffer = f"{buffer}\n\n{paragraph}".strip()
            continue
        if buffer:
            chunks.append({"text": buffer, "source": source, "doc_id": doc_id})
        if len(paragraph) <= CHUNK_SIZE:
            buffer = paragraph
        else:
            start = 0
            while start < len(paragraph):
                end = start + CHUNK_SIZE
                chunks.append({"text": paragraph[start:end], "source": source, "doc_id": doc_id})
                start = end - CHUNK_OVERLAP
            buffer = ""

    if buffer:
        chunks.append({"text": buffer, "source": source, "doc_id": doc_id})
    return chunks


def extract_pdf_text_from_bytes(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(page.strip() for page in pages if page.strip())


def _index_document(doc_id: str, filename: str, text: str) -> int:
    chunks = _chunk_text(text, filename, doc_id)
    if not chunks:
        return 0
    embeddings = embed_texts_safe([c["text"] for c in chunks])
    return upsert_chunks(doc_id, filename, chunks, embeddings)


def upload_pdf(content: bytes, filename: str) -> dict:
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported.")

    text = extract_pdf_text_from_bytes(content)
    if not text.strip():
        raise ValueError("Could not extract text from PDF. Ensure it is not a scanned image-only file.")

    doc_id = uuid.uuid4().hex[:12]
    safe_name = Path(filename).name
    chunk_count = _index_document(doc_id, safe_name, text)
    return add_document(doc_id=doc_id, filename=safe_name, chunk_count=chunk_count)


def list_documents_with_counts() -> list[dict]:
    docs = list_documents()
    for doc in docs:
        try:
            doc["chunk_count"] = count_chunks_for_doc(doc["id"])
        except ConnectionError:
            pass
    return docs


def delete_document(doc_id: str) -> bool:
    if not remove_doc_record(doc_id):
        return False
    delete_chunks_by_doc_id(doc_id)
    return True


def search_docs(query: str, k: int = 3) -> list[str]:
    query_embedding = embed_texts_safe([query])[0]
    hits = search_vectors(query_embedding, k=k)
    return [f"[{hit['source']}] {hit['text']}" for hit in hits]
