"""Decide whether a reply can go to the customer without a person.

Auto-send is stricter than standard review: every routing rule must be clear AND a set of extra
checks must pass. Anything money-, data- or security-related always goes to a person. Like routing,
this is plain code: the LLM never decides whether its own reply is safe to send.
"""
from __future__ import annotations

from opspilot import config


def auto_send_checks(classification: dict, retrieved: list[dict], queue: str,
                     draft: dict, injection: bool) -> list[tuple[str, bool]]:
    """Every check, with whether it passed. All must pass to send automatically."""
    best = max((h["score"] for h in retrieved), default=0.0)
    return [
        ("Auto-send is switched on", config.AUTO_SEND),
        ("All review rules clear (standard queue)", queue == "standard"),
        ("No prompt injection", not injection),
        ("Low risk", classification["risk"] == "low"),
        (f"Topic allowed for auto-send (not {', '.join(sorted(config.NEVER_AUTO_SEND))})",
         classification["category"] not in config.NEVER_AUTO_SEND),
        (f"Confidence at least {config.AUTO_SEND_MIN_CONFIDENCE}",
         classification["confidence"] >= config.AUTO_SEND_MIN_CONFIDENCE),
        (f"Strong source match (at least {config.AUTO_SEND_MIN_EVIDENCE})",
         best >= config.AUTO_SEND_MIN_EVIDENCE),
        ("Reply written by the LLM", draft.get("mode") == "llm"),
        ("Citation check passed", bool(draft.get("citation_ok"))),
    ]


def should_auto_send(checks: list[tuple[str, bool]]) -> bool:
    """True only when every check passed."""
    return bool(checks) and all(ok for _, ok in checks)
