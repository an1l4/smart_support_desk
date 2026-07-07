import json

from agents.llm import chat_completion
from models.schemas import AgentResponse, RoutedTicket, SupportRequest, TicketCategory
from tools.billing_lookup import explain_invoice, get_account_by_email
from tools.ticket_store import create_ticket, update_ticket

SYSTEM_PROMPT = """
You handle billing issues for a SaaS product. Always use the provided account data only.
Never invent charges, invoices, or payment history.
If the account is not found, ask the customer to verify their email.
If duplicate charges are mentioned, reference invoice statuses and explain next steps.
Be concise, empathetic, and professional.
"""


def handle(request: SupportRequest, routed: RoutedTicket) -> AgentResponse:
    ticket_id = create_ticket(
        category=TicketCategory.BILLING.value,
        customer_email=request.customer_email,
        subject=request.subject,
        message=request.message,
        metadata={"routing_confidence": routed.confidence, "routing_reason": routed.reasoning},
    )

    account = get_account_by_email(request.customer_email)
    if account is None:
        resolution = (
            f"We could not find a billing account for {request.customer_email}. "
            "Please verify the email used at checkout or contact support with your invoice ID."
        )
        update_ticket(ticket_id, status="needs_info", resolution=resolution)
        return AgentResponse(
            ticket_id=ticket_id,
            category=TicketCategory.BILLING,
            summary="Account not found",
            resolution=resolution,
            metadata={"account_found": False},
        )

    invoice_hints = [
        explain_invoice(request.customer_email, inv["id"])
        for inv in account.get("invoices", [])
    ]
    user_prompt = (
        f"Customer request:\nSubject: {request.subject}\nMessage: {request.message}\n\n"
        f"Account data:\n{json.dumps(account, indent=2)}\n\n"
        f"Invoice summaries:\n" + "\n".join(invoice_hints or ["No invoices on file."])
    )
    resolution = chat_completion(SYSTEM_PROMPT, user_prompt)
    summary = resolution.split(".")[0][:200]

    update_ticket(
        ticket_id,
        status="resolved",
        resolution=resolution,
        metadata={"account_found": True, "plan": account.get("plan")},
    )
    return AgentResponse(
        ticket_id=ticket_id,
        category=TicketCategory.BILLING,
        summary=summary,
        resolution=resolution,
        metadata={"account_found": True, "plan": account.get("plan")},
    )
