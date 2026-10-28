"""Thin wrapper around the LLM (Claude, or any OpenAI-compatible API). Callers must handle None (fallback)."""
from __future__ import annotations

import json
import os
import re
import threading
from datetime import date

from opspilot import config

# Public demo safety net: at most this many LLM calls per day (0 = no limit). Over the cap,
# callers get None and use the offline fallback, so a public URL can't run up the API bill.
_lock = threading.Lock()
_usage = {"day": None, "calls": 0}


def _take_daily_slot() -> bool:
    cap = int(os.getenv("OPSPILOT_LLM_DAILY_CAP", "0") or 0)
    if cap <= 0:
        return True
    with _lock:
        today = date.today()
        if _usage["day"] != today:
            _usage.update(day=today, calls=0)
        if _usage["calls"] >= cap:
            return False
        _usage["calls"] += 1
        return True


def ask_json(system: str, user: str, max_tokens: int = 800) -> dict | None:
    """Send one prompt and parse a JSON object from the reply. Returns None on any failure."""
    if not config.llm_enabled() or not _take_daily_slot():
        return None
    try:
        text = _anthropic(system, user, max_tokens) if config.LLM_PROVIDER == "anthropic" \
            else _openai_compatible(system, user, max_tokens)
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)  # some open models show reasoning
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except Exception:
        return None


def _anthropic(system: str, user: str, max_tokens: int) -> str:
    """Call the Claude Messages API and return the reply text."""
    import anthropic
    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model=config.LLM_MODEL, max_tokens=max_tokens, temperature=0,
        system=system, messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _openai_compatible(system: str, user: str, max_tokens: int) -> str:
    """Call an OpenAI-compatible /chat/completions endpoint (Groq, Gemini, OpenRouter...) with httpx."""
    import httpx
    r = httpx.post(
        f"{config.LLM_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.LLM_API_KEY}"},
        json={"model": config.LLM_MODEL, "temperature": 0,
              "max_tokens": max(max_tokens, 2000),  # reasoning models spend tokens before answering
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"] or ""
