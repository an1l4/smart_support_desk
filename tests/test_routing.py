from unittest.mock import MagicMock, patch

import pytest

from agents.master import route_request
from models.schemas import RoutedTicket, SupportRequest, TicketCategory


def _mock_completion(category: TicketCategory, confidence: float = 0.95) -> MagicMock:
    parsed = RoutedTicket(
        category=category,
        confidence=confidence,
        reasoning=f"Classified as {category.value}",
    )
    message = MagicMock()
    message.parsed = parsed
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


@pytest.mark.parametrize(
    "message,expected",
    [
        ("How do I reset my API key?", TicketCategory.PRODUCT),
        ("Why was I charged $59.99?", TicketCategory.BILLING),
        ("App crashes on login", TicketCategory.BUG),
    ],
)
def test_router(message, expected):
    request = SupportRequest(
        customer_email="test@example.com",
        subject="Support request",
        message=message,
    )
    with patch("agents.master.get_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.beta.chat.completions.parse.return_value = _mock_completion(expected)
        mock_get_client.return_value = mock_client

        result = route_request(request)

    assert result.category == expected
    assert result.confidence >= 0.7
