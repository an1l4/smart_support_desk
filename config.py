import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_PDFS_DIR = DATA_DIR / "sample_pdfs"
TICKETS_DB = DATA_DIR / "tickets.db"

openrouter_api_key = os.environ["OPENROUTER_API_KEY"]
openrouter_base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
openrouter_site_url = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8000")
openrouter_app_name = os.getenv("OPENROUTER_APP_NAME", "Smart Support Desk")
qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
router_model = os.getenv("ROUTER_MODEL", "openai/gpt-4o-mini")
agent_model = os.getenv("AGENT_MODEL", "openai/gpt-4o-mini")
embedding_model = os.getenv("EMBEDDING_MODEL", "openai/text-embedding-3-small")


class settings:
    """Namespace for application settings loaded from environment."""

    openrouter_api_key = openrouter_api_key
    openrouter_base_url = openrouter_base_url
    openrouter_site_url = openrouter_site_url
    openrouter_app_name = openrouter_app_name
    qdrant_url = qdrant_url
    router_model = router_model
    agent_model = agent_model
    embedding_model = embedding_model
