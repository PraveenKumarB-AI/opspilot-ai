"""Rule-based routing. The LLM never decides whether its own output needs review."""
from __future__ import annotations

from opspilot import config

ANGRY = ["unacceptable", "furious", "angry", "ridiculous", "cancel our contract", "escalate", "worst"]


def route(classification: dict, retrieved: list[dict], min_evidence: float,
          draft_check: dict | None, injection: bool, text: str) -> tuple[str, list[str]]:
    """Return ('standard' | 'priority', reasons). Every draft is still reviewed by a person."""
    reasons: list[str] = []
    if injection:
        reasons.append("Possible prompt injection in the request")
    if classification["risk"] == "high":
        reasons.append(f"High-risk request ({classification['category']})")
    if classification["confidence"] < config.CONFIDENCE_THRESHOLD:
        reasons.append(f"Low classification confidence ({classification['confidence']:.2f} "
                       f"< {config.CONFIDENCE_THRESHOLD})")
    best = max((h["score"] for h in retrieved), default=0.0)
    if best < min_evidence:
        reasons.append(f"Weak evidence (best match {best:.2f} < {min_evidence})")
    if draft_check is not None and not draft_check["citation_ok"]:
        reasons.append("Citation check failed: " + "; ".join(draft_check["issues"]))
    if classification["urgency"] == "high":
        reasons.append("Urgent request")
    if any(w in text.lower() for w in ANGRY):
        reasons.append("Upset or escalating customer")
    return ("priority" if reasons else "standard"), reasons
