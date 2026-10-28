"""Holding replies: a professional first response when OpsPilot must not answer the question itself.

Used for high-risk requests (money, data, security, tax, outages), possible prompt injection, vague
messages, and questions the help articles don't cover. A holding reply states no product facts, so it
can't be wrong about the product: it acknowledges the customer, says who will handle the request,
and asks for anything that will speed it up. A person always reviews it before it goes out (it is
never auto-sent), and can escalate the case at the same time.
"""
from __future__ import annotations

from opspilot.classifier import OUTAGE_TERMS

GENERIC = "A member of our support team will review your request carefully and reply to you directly."

REPLIES = {
    "security": (
        "We treat possible security issues as a priority, and our "
        "security team has been asked to review it straight away.\n\n"
        "As a precaution, please change your password and check that only the people who need access "
        "to your account have it. We will update you as soon as we know more."),
    "data_privacy": (
        "Requests to delete, export or retain customer data are handled "
        "by our data protection team, who must verify every request before anything is changed.\n\n"
        "They will contact you to confirm the scope and the next steps. No data will be changed until "
        "that confirmation is complete."),
    "billing": (
        "Refunds, credits and billing corrections are reviewed by our "
        "Billing team, so your request has been passed to them.\n\n"
        "They will review your account and reply with the outcome. If you haven't already, please "
        "reply with the invoice number and the dates involved; it will help them resolve this faster."),
    "tax": (
        "Tax questions such as filing deadlines and book-to-tax treatment are answered by our tax "
        "specialists, so yours has been passed to them.\n\n"
        "They will reply with guidance that fits your setup."),
    "outage": (
        "We understand this is stopping your work, and it has been flagged as urgent. Our engineers "
        "are looking into it now, and we will send you an update as soon as we have one.\n\n"
        "If you can, please reply with any error message you see and the time the problem started; "
        "that will help us resolve it faster."),
    "high_risk": (
        "Because this needs careful handling, your request has been passed to a "
        "senior specialist who will review the details and reply to you directly."),
    "unclear": (
        "So we can help quickly, could you tell us a little more?\n\n"
        "- What were you trying to do?\n"
        "- Which screen or report were you using?\n"
        "- Did you see an error message? If so, what did it say?\n\n"
        "Once we have these details, we'll get back to you with an answer."),
    "not_covered": (
        "Your question isn't covered in our help articles, so it has been passed to "
        "a specialist who can give you an accurate answer. They will reply to you directly."),
}


def holding_kind(classification: dict, text: str, injection: bool) -> str:
    """Pick the right holding reply. Order matters: the most sensitive reason wins."""
    t = text.lower()
    category = classification.get("category", "general")
    if injection:
        return "generic"  # never engage with instructions hidden in the message
    if category in ("security", "data_privacy", "billing", "tax"):
        return category
    if classification.get("urgency") == "high" or any(f" {w}" in f" {t}" for w in OUTAGE_TERMS):
        return "outage"
    if classification.get("risk") == "high":
        return "high_risk"
    if category == "general" and len(t.split()) < 15:
        return "unclear"
    return "not_covered"


def holding_reply(classification: dict, text: str, injection: bool) -> dict:
    """A draft record in the same shape as draft_response(): {'text', 'mode', 'kind'}."""
    kind = holding_kind(classification, text, injection)
    return {"text": REPLIES.get(kind, GENERIC), "mode": "holding", "kind": kind}
