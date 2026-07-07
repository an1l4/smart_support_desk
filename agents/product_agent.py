from agents.llm import chat_completion
from models.schemas import AgentResponse, RoutedTicket, SupportRequest, TicketCategory
from tools.doc_search import search_docs
from tools.ticket_store import create_ticket, update_ticket

SYSTEM_PROMPT = """
You answer product questions using ONLY the documentation excerpts provided.
If the docs do not contain enough information, say so clearly and suggest contacting human support.
Cite which document source you used when answering.
Be concise and accurate. Do not invent features or policies.
"""


def handle(request: SupportRequest, routed: RoutedTicket) -> AgentResponse:
    ticket_id = create_ticket(
        category=TicketCategory.PRODUCT.value,
        customer_email=request.customer_email,
        subject=request.subject,
        message=request.message,
        metadata={"routing_confidence": routed.confidence, "routing_reason": routed.reasoning},
    )

    doc_chunks = search_docs(f"{request.subject}\n{request.message}")
    if not doc_chunks:
        resolution = (
            "I could not find relevant documentation for your question. "
            "An administrator may need to upload product PDFs via POST /docs/upload. "
            "Please contact support and include any error messages you see."
        )
        update_ticket(ticket_id, status="needs_info", resolution=resolution)
        return AgentResponse(
            ticket_id=ticket_id,
            category=TicketCategory.PRODUCT,
            summary="No matching documentation found",
            resolution=resolution,
            metadata={"sources": []},
        )

    context = "\n\n---\n\n".join(doc_chunks)
    user_prompt = (
        f"Customer question:\nSubject: {request.subject}\nMessage: {request.message}\n\n"
        f"Documentation excerpts:\n{context}"
    )
    resolution = chat_completion(SYSTEM_PROMPT, user_prompt)
    sources = [chunk.split("]", 1)[0].strip("[") for chunk in doc_chunks if chunk.startswith("[")]

    update_ticket(
        ticket_id,
        status="resolved",
        resolution=resolution,
        metadata={"sources": sources},
    )
    return AgentResponse(
        ticket_id=ticket_id,
        category=TicketCategory.PRODUCT,
        summary=resolution.split(".")[0][:200],
        resolution=resolution,
        metadata={"sources": sources},
    )
