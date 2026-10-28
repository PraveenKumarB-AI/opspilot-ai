"""Turn an approved reply into the email the customer receives.

Reviewers work with the tagged draft ("... [KB-07 §2]") so they can check every claim. Customers get
a clean, professional email: greeting, the answer without tags, the help articles it relied on, and
a signature. The tagged text stays in the database and audit trail.
"""
from __future__ import annotations

import re

COMPANY = "PraveenPlan"
SIGNATURE = f"Best regards,\n{COMPANY} Customer Support"
TAG = re.compile(r"\s*\[KB-\d+[^\]]*\]")
GENERIC_NAMES = {"", "customer", "demo", "demo customer", "user", "test"}


def strip_tags(text: str) -> str:
    """Remove citation tags like [KB-07 §2] and tidy the spacing they leave behind."""
    clean = TAG.sub("", text)
    clean = re.sub(r"[ \t]+([.,;:!?])", r"\1", clean)
    return re.sub(r"[ \t]{2,}", " ", clean).strip()


OPENERS = re.compile(r"^(hi|hello|hey|dear)\b[^.!?]*,?$|^thanks?( you)? for (contacting|reaching|getting)", re.I)
CLOSERS = re.compile(r"^((best|kind|warm)?\s*regards|thanks|thank you|cheers|sincerely)[,.!]?$|"
                     r"^(the )?(support|customer support)( team)?[,.]?$|^let us know\b|^please let us know\b", re.I)


def body_only(text: str) -> str:
    """Drop greeting and sign-off lines a draft (or a reviewer) already wrote, so the email has one of each."""
    lines = [ln.rstrip() for ln in text.strip().splitlines()]
    while lines and (not lines[0].strip() or OPENERS.search(lines[0].strip())):
        lines.pop(0)
    while lines and (not lines[-1].strip() or CLOSERS.search(lines[-1].strip())):
        lines.pop()
    return "\n".join(lines).strip()


def greeting(customer: str) -> str:
    """'Hi Maria,' for a real first name, otherwise 'Hello,'."""
    name = (customer or "").strip()
    first = name.split()[0] if name else ""
    if name.lower() in GENERIC_NAMES or not first.isalpha():
        return "Hello,"
    return f"Hi {first.capitalize()},"


def cited_articles(draft_text: str, evidence: list[dict]) -> list[str]:
    """Titles of the help articles the reply cites, in the order they were retrieved, no duplicates."""
    cited = {m.group(0).strip(" []").split()[0] for m in TAG.finditer(draft_text)}  # e.g. "KB-07"
    out: list[str] = []
    for e in evidence:
        doc = e["chunk_id"].split()[0]
        title = e["title"].split(":")[0].strip()
        line = f"{doc}: {title}"
        if doc in cited and line not in out:
            out.append(line)
    return out


def compose_email(request_id: int, customer: str, subject: str, reply_text: str,
                  evidence: list[dict], holding: bool = False) -> dict:
    """Build the customer email from the reviewed (tagged) reply text."""
    body = body_only(strip_tags(reply_text))
    articles = cited_articles(reply_text, evidence)
    parts = [
        greeting(customer),
        f'Thank you for contacting {COMPANY} Support about "{subject.strip()}".',
        body,
    ]
    if articles:
        parts.append("For more detail, see these help articles:\n" + "\n".join(f"- {a}" for a in articles))
    if holding:  # the answer is still to come, so invite more detail instead
        parts.append("If you have anything to add in the meantime, simply reply to this email.")
    else:
        parts.append("If this doesn't resolve the issue, simply reply to this email and a member of our "
                     "team will follow up.")
    parts.append(f"{SIGNATURE}\nTicket #{request_id}")
    return {"subject": f"Re: {subject.strip()} [Ticket #{request_id}]", "body": "\n\n".join(parts)}
