"""Central settings for OpsPilot AI. Change thresholds here, not in the code that uses them."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

KNOWLEDGE_DIR = ROOT / "data" / "knowledge"
REQUESTS_CSV = ROOT / "data" / "requests" / "test_requests.csv"
DB_PATH = Path(os.getenv("OPSPILOT_DB", ROOT / "opspilot.db"))

# "auto" uses the Claude API when a key is set, otherwise the deterministic fallback.
# "fallback" always uses the fallback (used by tests so they are free and repeatable).
MODE = os.getenv("OPSPILOT_MODE", "auto").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
LLM_MODEL = os.getenv("OPSPILOT_LLM_MODEL", "claude-sonnet-5-5")

# Embeddings: "tfidf" (default, tested, offline) or "auto" / "sentence-transformers" (optional upgrade:
# pip install sentence-transformers, then re-tune MIN_EVIDENCE_SCORE with the eval).
EMBEDDINGS = os.getenv("OPSPILOT_EMBEDDINGS", "tfidf").lower()
ST_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Routing thresholds. The TF-IDF value was set from the synthetic eval (normal requests all
# scored >= 0.206; most no-answer requests <= 0.20). The sentence-transformers value is a
# starting guess: re-tune it with `python -m eval.run_eval` after installing that package.
CONFIDENCE_THRESHOLD = 0.85
MIN_EVIDENCE_SCORE = {"sentence-transformers": 0.35, "tfidf": 0.20}
TOP_K = 4

HIGH_RISK_CATEGORIES = {"billing", "data_privacy", "security"}


def llm_enabled() -> bool:
    """True when drafting and classification should call the Claude API."""
    return MODE != "fallback" and bool(ANTHROPIC_API_KEY)
