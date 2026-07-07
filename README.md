# Smart Support Desk

Master + sub-agent support system with PDF-based product knowledge stored in **Qdrant** vector database.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `.env` (copy from `.env.example`):

```env
OPENROUTER_API_KEY=sk-or-your-key-here
QDRANT_URL=http://localhost:6333
ROUTER_MODEL=openai/gpt-4o-mini
AGENT_MODEL=openai/gpt-4o-mini
EMBEDDING_MODEL=openai/text-embedding-3-small
```

## Start Qdrant (vector database)

```bash
docker compose up -d
```

- **Qdrant Web UI:** http://localhost:6333/dashboard
- Browse collection `product_doc_chunks` to see uploaded PDF chunks and vectors

## Run API

```bash
uvicorn main:app --reload
```

- **Swagger UI:** http://127.0.0.1:8000/docs
- **Postman:** import `postman/Smart_Support_Desk.postman_collection.json`
- **Health check:** http://127.0.0.1:8000/health (shows Qdrant connection status)

## Knowledge base (PDF upload → Qdrant)

```bash
# Generate sample PDFs
python scripts/generate_sample_pdfs.py

# Bulk upload samples into Qdrant (requires OpenAI key + Qdrant running)
python scripts/seed_knowledge_base.py
```

Or upload via Swagger `POST /docs/upload` or Postman.

## How it works

```
PDF upload → extract text → chunk → OpenAI embeddings → Qdrant vector DB
Product question → embed query → Qdrant similarity search → LLM answer
```

## Example scenarios

**Product:** Upload `02-api-rate-limits.pdf`, then ask "What's the API rate limit on the Pro plan?"

**Billing:** `alice@example.com` — "I was charged twice for June."

**Bug:** "The dashboard goes blank after I upload a CSV."

## Tests

```bash
pytest tests/ -v
```

## Stop Qdrant

```bash
docker compose down
```

# Tests

## step 1 

```bash
cd /Users/anilasoman/Documents/ai_learning/smart_support_desk
source .venv/bin/activate
pip install -r requirements.txt
```

## step 2

varify .env

## step 3 

generate sample pdf (if not there)
```bash
python scripts/generate_sample_pdfs.py
```
This creates 9 PDFs in data/sample_pdfs/.

## step 4
```bash
docker compose up -d
```

## step 5

```bash 
source .venv/bin/activate
uvicorn main:app --reload
```

## step 6

system health

http://127.0.0.1:8000/health

url for qdrant_ui : http://localhost:6333/dashboard
swagger _ui : http://127.0.0.1:8000/docs

## step 7

upload pdf 
optional using script : python scripts/seed_knowledge_base.py

POST /docs/upload

## step 8

GET /docs/list

## step 9

support scenarios

POST /support

scenari 1
-----------

{
  "customer_email": "bob@example.com",
  "subject": "API rate limits",
  "message": "What's the API rate limit on the Pro plan?"
}

Expected:

category: "product_question"
Answer mentions Pro plan limit (1,000 requests/minute)
metadata.sources includes 02-api-rate-limits.pdf

-------------------------------------------------------------------
scenari 2
-----------
{
  "customer_email": "bob@example.com",
  "subject": "API key help",
  "message": "How do I reset my API key?"
}

Expected:

category: "product_question"
Answer references Settings → API → Keys steps
metadata.sources includes 03-api-keys.pdf
--------------------------------------------------------------------

scenari 3
-----------
{
  "customer_email": "bob@example.com",
  "subject": "Webhook retries",
  "message": "How does webhook retry work if my endpoint is down?"
}

Expected:

category: "product_question"
Answer mentions retry intervals (1 min, 5 min, 30 min, etc.)

---------------------------------------------------------------------
scenari 4
-----------

{
  "customer_email": "bob@example.com",
  "subject": "Cannot login",
  "message": "I forgot my password and the reset link expired."
}

Expected:

category: "product_question"
Answer references forgot password / 1-hour expiry
---------------------------------------------------------------------
scenari 5
-----------
{
  "customer_email": "alice@example.com",
  "subject": "Double charged",
  "message": "I was charged twice for June."
}

Expected:

category: "billing_issue"
Answer references Alice's account and invoices INV-101, INV-102
INV-102 status: pending_review
metadata.account_found: true
metadata.plan: "pro"

---------------------------------------------------------------------
scenari 6
-----------
{
  "customer_email": "grace@example.com",
  "subject": "Outstanding balance",
  "message": "Why do I have an unpaid invoice?"
}

Expected:

category: "billing_issue"
Answer references Grace's balance and unpaid invoice

---------------------------------------------------------------------
scenari 7
-----------
{
  "customer_email": "unknown@example.com",
  "subject": "Billing question",
  "message": "Why was I charged?"
}

Expected:

category: "billing_issue"
summary: account not found message
metadata.account_found: false

---------------------------------------------------------------------
scenari 8
-----------
{
  "customer_email": "bob@example.com",
  "subject": "Dashboard crash",
  "message": "The dashboard goes blank after I upload a CSV file."
}


Expected:

category: "bug_report"
metadata.severity: "high" or "medium"
ticket_id: e.g. TKT-XXXXXXXX
Resolution includes next steps for engineering

---------------------------------------------------------------------
scenari 9
-----------
{
  "customer_email": "dave@example.com",
  "subject": "Security issue",
  "message": "Other users can see my private project data without permission."
}

Expected:

category: "bug_report"
metadata.severity: "critical" or "high"

---------------------------------------------------------------------

## step 10

Delete a PDF
GET /docs/list → copy a doc_id
DELETE /docs/{doc_id} → paste the id → Execute
Check Qdrant UI — chunks for that doc should be gone
Ask a product question about that doc → should not find answer