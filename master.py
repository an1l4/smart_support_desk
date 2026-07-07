from models.schemas import RoutedTicket, SupportRequest
from agents.llm import get_client
from config import settings

ROUTER_PROMPT = """
You are a support ticket router. Classify the request into exactly one category:
- product_question: how-to, features, documentation
- billing_issue: payments, invoices, refunds, plan changes, duplicate charges
- bug_report: errors, crashes, broken behavior, unexpected failures

Return JSON with category, confidence (0-1), and brief reasoning.
"""


def route_request(request: SupportRequest) -> RoutedTicket:
    user_content = (
        f"Customer email: {request.customer_email}\n"
        f"Subject: {request.subject}\n"
        f"Message: {request.message}"
    )
    completion = get_client().beta.chat.completions.parse(
        model=settings.router_model,
        messages=[
            {"role": "system", "content": ROUTER_PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format=RoutedTicket,
        temperature=0, # makes the routing consistent and predictable.
    )
    parsed = completion.choices[0].message.parsed

    # Error handling
    if parsed is None:
        raise RuntimeError("Router failed to return a structured classification.")
    return parsed
