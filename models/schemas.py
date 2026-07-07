# typed contracts so every agent returns the same shape.
# Routing, logging, and API responses all depend on these models.

from enum import Enum
from pydantic import BaseModel, Field

class TicketCategory(str, Enum):
    PRODUCT = "product_question"
    BILLING = "billing_issue"
    BUG = "bug_report"

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SupportRequest(BaseModel):
    customer_email: str = Field(..., examples=["alice@example.com"]) # ... means required.
    subject: str = Field(..., examples=["API rate limits"]) # examples are mainly used by documentation tools like FastAPI's Swagger UI. They help users understand the expected input but are not validation rules
    message: str = Field(
        ...,
        examples=["What's the API rate limit on the Pro plan?"],
    )


class DocumentInfo(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    chunk_count: int


class DocUploadResponse(BaseModel):
    message: str
    document: DocumentInfo

class RoutedTicket(BaseModel):
    category: TicketCategory
    confidence: float = Field(ge=0, le=1)
    reasoning: str

class AgentResponse(BaseModel):
    ticket_id: str
    category: TicketCategory
    summary: str
    resolution: str
    metadata: dict = {}


class BugTriageResult(BaseModel):
    severity: Severity
    summary: str
    resolution: str
    reproduction_notes: str = ""