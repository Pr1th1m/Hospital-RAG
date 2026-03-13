"""
Centralized configuration – all env vars and constants in one place.
"""

import logging
import os

from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# ── Retrieval ────────────────────────────────────────────────────────
RETRIEVAL_TOP_K = max(1, int(os.getenv("RETRIEVAL_TOP_K", "8")))

# ── Admin ────────────────────────────────────────────────────────────
ADMIN_TOKEN_TTL_MINUTES = max(5, int(os.getenv("ADMIN_TOKEN_TTL_MINUTES", "120")))
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# ── Tavily (web search) ─────────────────────────────────────────────
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
tavily_client = TavilyClient(api_key=TAVILY_API_KEY) if TAVILY_API_KEY else None
