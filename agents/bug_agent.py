from agents.llm import get_client
from config import settings
from models.schemas import (
    AgentResponse,
    BugTriageResult,
    RoutedTicket,
    SupportRequest,
    TicketCategory,
)
from tools.ticket_store import create_ticket, update_ticket

SYSTEM_PROMPT = """
You triage software bug reports. Assign severity using these rules:
- critical: data loss, security issue, or complete service outage
- high: major feature broken with no reasonable workaround
- medium: feature impaired but a workaround exists
- low: cosmetic issue or rare edge case

Extract a short summary, reproduction notes if mentioned, and clear next steps for engineering.
"""


def handle(request: SupportRequest, routed: RoutedTicket) -> AgentResponse:
    user_prompt = (
        f"Bug report:\nSubject: {request.subject}\n"
        f"Customer: {request.customer_email}\n"
        f"Message: {request.message}"
    )
    completion = get_client().beta.chat.completions.parse(
        model=settings.agent_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format=BugTriageResult,
        temperature=0.2,
    )
    triage = completion.choices[0].message.parsed
    if triage is None:
        raise RuntimeError("Bug triage agent failed to return structured output.")

    ticket_id = create_ticket(
        category=TicketCategory.BUG.value,
        customer_email=request.customer_email,
        subject=request.subject,
        message=request.message,
        severity=triage.severity.value,
        status="triaged",
        resolution=triage.resolution,
        metadata={
            "routing_confidence": routed.confidence,
            "routing_reason": routed.reasoning,
            "reproduction_notes": triage.reproduction_notes,
        },
    )

    return AgentResponse(
        ticket_id=ticket_id,
        category=TicketCategory.BUG,
        summary=triage.summary,
        resolution=triage.resolution,
        metadata={
            "severity": triage.severity.value,
            "reproduction_notes": triage.reproduction_notes,
        },
    )
