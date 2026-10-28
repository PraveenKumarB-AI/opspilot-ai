"""Thin wrapper around the Claude API. Every caller must handle a None result (fallback)."""
from __future__ import annotations

import json
import re

from opspilot import config


def ask_json(system: str, user: str, max_tokens: int = 800) -> dict | None:
    """Send one prompt and parse a JSON object from the reply. Returns None on any failure."""
    if not config.llm_enabled():
        return None
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.LLM_MODEL, max_tokens=max_tokens, temperature=0,
            system=system, messages=[{"role": "user", "content": user}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group(0)) if match else None
    except Exception:
        return None
