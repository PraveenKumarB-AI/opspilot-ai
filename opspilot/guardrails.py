"""Safety checks that are plain code, so they are predictable and testable."""
from __future__ import annotations

import re

INJECTION_PATTERNS = [
    r"ignore (all |your |the )?(above |previous |prior |earlier )?(instructions|rules|directions|prompt)",
    r"disregard (your|the|all|any) (rules|instructions|policy|directions)",
    r"forget (everything|all) (you|your|previous|prior|that)", r"forget your (instructions|rules)",
    r"new (rule|instruction)s?:",
    r"(^|\n)\s*(system|assistant|developer)\s*:",
    r"you are now", r"system prompt", r"pretend (to be|you are)",
    r"you are (now )?(authori[sz]ed|allowed|permitted) to",
    r"approve (this|it|a full|the) (refund|credit) (now|immediately|automatically)",
    r"act as (an? )?(admin|administrator|developer)",
]
CITATION = re.compile(r"\[(KB-\d{2} §\d+)\]")
NUMBER = re.compile(r"\b\d+(?:[.,]\d+)*\b")
# Split after . ! ? or a closing citation tag, but keep a tag attached to the sentence before it.
SENTENCE = re.compile(r"(?<=[.!?\]])\s+(?!\[)|\n+")
# An uncited sentence containing one of these is a claim that must come from a source.
COMMITMENTS = ["refund", "credit", "approve", "approved", "delete", "deleted", "guarantee",
               "we will", "you will", "eligible", "waive"]


def detect_injection(text: str) -> bool:
    """True if the request tries to override the assistant's instructions.
    Whitespace is collapsed first, so extra spaces or line breaks don't hide a phrase."""
    t = " ".join(text.lower().split())
    lines = text.lower()
    return any(re.search(p, t) or re.search(p, lines) for p in INJECTION_PATTERNS)


def extract_citations(draft: str) -> list[str]:
    """All citation tags in a draft, e.g. ['KB-07 §2']."""
    return CITATION.findall(draft)


def uncited_claims(draft: str) -> list[str]:
    """Sentences with no citation that contain a number or a commitment word."""
    text = re.sub(r'"[^"]*"', '""', draft)  # ignore quoted text such as the customer's subject
    out = []
    for s in SENTENCE.split(text):
        s = s.strip()
        if not s or CITATION.search(s):
            continue
        low = s.lower()
        if NUMBER.search(s) or any(re.search(rf"\b{re.escape(w)}\b", low) for w in COMMITMENTS):
            out.append(s)
    return out


def check_draft(draft: str, retrieved: list[dict]) -> dict:
    """Verify citations, numbers and uncited claims against the retrieved sources."""
    issues: list[str] = []
    cited = extract_citations(draft)
    allowed = {h["chunk_id"] for h in retrieved}
    if not cited:
        issues.append("Draft has no citations")
    bad = sorted(set(cited) - allowed)
    if bad:
        issues.append(f"Cites sources that were not retrieved: {', '.join(bad)}")
    source_numbers = set(NUMBER.findall(" ".join(h["text"] for h in retrieved
                                                 if h["chunk_id"] in set(cited))))
    body = CITATION.sub("", draft)
    unsupported = sorted({n for n in NUMBER.findall(body) if n not in source_numbers})
    if unsupported:
        issues.append(f"Numbers not found in cited sources: {', '.join(unsupported)}")
    claims = uncited_claims(draft)
    if claims:
        issues.append(f"Uncited claim: {claims[0][:80]}")
    return {"citations": cited, "citation_ok": not issues, "issues": issues}
