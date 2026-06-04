"""Runtime settings for the chat API, loaded from environment / .env.

Provider-specific keys and models live in providers.py; this just selects the active
provider and a few shared knobs.
"""
import os
from functools import lru_cache

try:
    from dotenv import load_dotenv
    load_dotenv()  # load .env from repo root if present; no-op otherwise
except Exception:  # python-dotenv optional at import time
    pass


@lru_cache(maxsize=1)
def get_settings() -> dict:
    return {
        "provider": os.getenv("CHAT_PROVIDER", "perplexity").strip().lower(),
        "top_k": int(os.getenv("CHAT_TOP_K", "6")),
        "cors_origin": os.getenv("CHAT_CORS_ORIGIN", "http://localhost:8000").strip(),
    }
