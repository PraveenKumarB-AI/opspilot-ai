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

# "auto" uses an LLM when a key is set, otherwise the deterministic fallback.
# "fallback" always uses the fallback (used by tests so they are free and repeatable).
MODE = os.getenv("OPSPILOT_MODE", "auto").lower()

# LLM provider: "anthropic" (Claude API) or "openai" (any OpenAI-compatible endpoint, e.g. Groq's
# free tier). The rest of the app does not care which one answers: both go through opspilot/llm.py.
LLM_PROVIDER = os.getenv("OPSPILOT_LLM_PROVIDER", "anthropic").lower()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
LLM_API_KEY = os.getenv("OPSPILOT_LLM_API_KEY", "").strip()           # for provider "openai"
LLM_BASE_URL = os.getenv("OPSPILOT_LLM_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
LLM_MODEL = os.getenv("OPSPILOT_LLM_MODEL",
                      "claude-sonnet-5-5" if LLM_PROVIDER == "anthropic" else "openai/gpt-oss-120b")

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

# Auto-send: replies that pass every check go to the customer without a person. Stricter than
# standard review on purpose. Turn off with OPSPILOT_AUTO_SEND=off (everything then needs a person).
AUTO_SEND = os.getenv("OPSPILOT_AUTO_SEND", "on").lower() in {"on", "1", "true", "yes"}
AUTO_SEND_MIN_CONFIDENCE = 0.90
AUTO_SEND_MIN_EVIDENCE = 0.30
NEVER_AUTO_SEND = {"billing", "data_privacy", "security", "tax", "general"}

# Topics that are always high risk. Billing and privacy are high risk only when the request asks for
# something risky (refund, deletion, ...), so routine questions like "update billing contact" are not.
HIGH_RISK_CATEGORIES = {"security"}


def llm_key() -> str:
    """The API key for the selected provider ("" when none is set)."""
    return ANTHROPIC_API_KEY if LLM_PROVIDER == "anthropic" else LLM_API_KEY


def llm_enabled() -> bool:
    """True when drafting and classification should call an LLM."""
    return MODE != "fallback" and LLM_PROVIDER in {"anthropic", "openai"} and bool(llm_key())


def llm_label() -> str:
    """Who writes the drafts, for the UI: e.g. "Claude (claude-sonnet-5-5)" or "openai/gpt-oss-120b via Groq"."""
    if not llm_enabled():
        return "Fallback mode (no API key)"
    if LLM_PROVIDER == "anthropic":
        return f"Claude ({LLM_MODEL})"
    host = LLM_BASE_URL.split("//")[-1].split("/")[0]
    name = "Groq" if "groq" in host else host
    return f"{LLM_MODEL} via {name}"
