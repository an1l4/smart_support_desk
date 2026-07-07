import argparse
import json

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from agents import billing_agent, bug_agent, product_agent
from agents.master import route_request
from models.schemas import (
    AgentResponse,
    DocUploadResponse,
    DocumentInfo,
    SupportRequest,
    TicketCategory,
)
from tools.billing_lookup import seed_billing_data
from tools.doc_search import delete_document, list_documents_with_counts, upload_pdf
from tools.embeddings import EmbeddingError
from tools.vector_store import ensure_collection, is_healthy

app = FastAPI(
    title="Smart Support Desk API",
    description=(
        "Master + sub-agent support system. Upload product documentation as PDFs "
        "into Qdrant vector DB, then submit support requests via POST /support.\n\n"
        "**Quick start:**\n"
        "1. `docker compose up -d` (starts Qdrant)\n"
        "2. Open Qdrant UI: http://localhost:6333/dashboard\n"
        "3. Upload PDFs at `POST /docs/upload`\n"
        "4. Submit a ticket at `POST /support`"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_seed_billing() -> None:
    """Ensure billing tables and Qdrant collection exist."""
    seed_billing_data()
    try:
        ensure_collection()
    except ConnectionError:
        pass  # Qdrant may not be running yet; upload will show a clear error


# orchestrator
def handle_support_request(request: SupportRequest) -> AgentResponse:
    routed = route_request(request)

    if routed.category == TicketCategory.PRODUCT:
        return product_agent.handle(request, routed)
    if routed.category == TicketCategory.BILLING:
        return billing_agent.handle(request, routed)
    return bug_agent.handle(request, routed)


@app.get("/health", tags=["System"])
def health() -> dict:
    """Check if the API and Qdrant vector DB are running."""
    return {
        "status": "ok",
        "qdrant": "connected" if is_healthy() else "disconnected",
        "qdrant_ui": "http://localhost:6333/dashboard",
    }


@app.post(
    "/docs/upload",
    response_model=DocUploadResponse,
    tags=["Knowledge Base"],
    summary="Upload a product documentation PDF",
)
async def upload_document(file: UploadFile = File(..., description="PDF file to index")) -> DocUploadResponse:
    """
    Upload a PDF for the product agent knowledge base.

    The PDF is processed in memory, chunked, embedded via OpenRouter,
    and stored in the Qdrant vector database. View chunks in the Qdrant UI.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        doc = upload_pdf(content, file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except EmbeddingError as exc:
        raise HTTPException(status_code=402, detail=str(exc)) from exc

    return DocUploadResponse(
        message="PDF uploaded and indexed successfully.",
        document=DocumentInfo(**doc),
    )


@app.get(
    "/docs/list",
    response_model=list[DocumentInfo],
    tags=["Knowledge Base"],
    summary="List uploaded documentation PDFs",
)
def get_documents() -> list[DocumentInfo]:
    """Return all PDFs currently in the knowledge base."""
    return [DocumentInfo(**doc) for doc in list_documents_with_counts()]


@app.delete(
    "/docs/{doc_id}",
    tags=["Knowledge Base"],
    summary="Delete an uploaded PDF from the knowledge base",
)
def remove_document(doc_id: str) -> dict:
    """Remove a PDF and rebuild the search index."""
    if not delete_document(doc_id):
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return {"message": f"Document '{doc_id}' deleted and index rebuilt."}


@app.post(
    "/support",
    response_model=AgentResponse,
    tags=["Support"],
    summary="Submit a support request",
)
def create_support_ticket(request: SupportRequest) -> AgentResponse:
    """
    Submit a support ticket. The master router classifies it as:

    - **product_question** → searches uploaded PDF docs
    - **billing_issue** → looks up account data
    - **bug_report** → triages severity and logs ticket
    """
    return handle_support_request(request)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smart Support Desk CLI")
    parser.add_argument("--email", required=True, help="Customer email")
    parser.add_argument("--subject", required=True, help="Ticket subject")
    parser.add_argument("--message", required=True, help="Ticket message")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    req = SupportRequest(
        customer_email=args.email,
        subject=args.subject,
        message=args.message,
    )
    result = handle_support_request(req)
    print(json.dumps(result.model_dump(), indent=2))
