import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    VectorParams,
)

from config import settings
from tools.embeddings import get_embedding_dimensions

COLLECTION_NAME = "product_doc_chunks"


def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection() -> None:
    """Create the Qdrant collection if it does not exist."""
    try:
        client = get_client()
    except Exception as exc:
        raise ConnectionError(
            "Cannot connect to Qdrant. Start it with: docker compose up -d"
        ) from exc

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=get_embedding_dimensions(),
                distance=Distance.COSINE,
            ),
        )


def upsert_chunks(
    doc_id: str,
    filename: str,
    chunks: list[dict],
    embeddings: list[list[float]],
) -> int:
    """Store document chunks as vectors in Qdrant."""
    ensure_collection()
    client = get_client()

    delete_chunks_by_doc_id(doc_id)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={
                "doc_id": doc_id,
                "source": filename,
                "text": chunk["text"],
                "chunk_index": index,
            },
        )
        for index, (chunk, embedding) in enumerate(zip(chunks, embeddings))
    ]

    if points:
        client.upsert(collection_name=COLLECTION_NAME, points=points)

    return len(points)


def search_vectors(query_vector: list[float], k: int = 3) -> list[dict]:
    """Return top-k matching chunks from Qdrant."""
    ensure_collection()
    client = get_client()

    response = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=k,
        with_payload=True,
    )

    return [
        {
            "source": hit.payload["source"],
            "text": hit.payload["text"],
            "score": hit.score,
        }
        for hit in response.points
        if hit.payload
    ]


def delete_chunks_by_doc_id(doc_id: str) -> None:
    """Remove all vector chunks for a document."""
    ensure_collection()
    client = get_client()
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
    )


def count_chunks_for_doc(doc_id: str) -> int:
    """Count indexed chunks for a document."""
    ensure_collection()
    client = get_client()
    result = client.count(
        collection_name=COLLECTION_NAME,
        count_filter=Filter(
            must=[FieldCondition(key="doc_id", match=MatchValue(value=doc_id))]
        ),
        exact=True,
    )
    return result.count


def is_healthy() -> bool:
    """Check if Qdrant is reachable."""
    try:
        client = get_client()
        client.get_collections()
        return True
    except Exception:
        return False
