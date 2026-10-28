"""process_request(): the end-to-end flow used by the API, the tests and the evaluation."""
from __future__ import annotations

import json
import sqlite3

from opspilot import config, db
from opspilot.autosend import auto_send_checks, should_auto_send
from opspilot.classifier import classify
from opspilot.drafter import NO_DRAFT, draft_response
from opspilot.guardrails import check_draft, detect_injection
from opspilot.mailer import compose_email
from opspilot.retriever import get_retriever
from opspilot.router import route


AUTO_REVIEWER = "OpsPilot (automatic)"


def process_request(conn: sqlite3.Connection, subject: str, body: str,
                    customer: str = "Demo customer", channel: str = "web") -> dict:
    """Classify, retrieve, draft, check and route one request; store and audit every step."""
    request_id = db.insert_request(conn, customer, channel, subject, body)
    db.log(conn, request_id, "request_received", {"customer": customer, "channel": channel})
    try:
        _run_steps(conn, request_id, subject, body)
    except Exception as exc:  # never leave a saved request outside every queue
        _route_after_error(conn, request_id, exc)
    return get_request(conn, request_id)


def _run_steps(conn: sqlite3.Connection, request_id: int, subject: str, body: str) -> None:
    """Classify, retrieve, draft, check and route. Any exception is handled by the caller."""
    text = f"{subject}\n{body}"

    classification = classify(text)
    db.save_classification(conn, request_id, classification)
    db.log(conn, request_id, "classified", classification)

    retriever = get_retriever()
    hits = retriever.search(text)
    db.save_retrievals(conn, request_id, hits)
    db.log(conn, request_id, "retrieved", {"chunks": [h["chunk_id"] for h in hits],
                                           "scores": [h["score"] for h in hits]})

    injection = detect_injection(text)
    evidence = [h for h in hits if h["score"] >= retriever.min_evidence]
    if injection or not evidence or classification["category"] == "general":
        draft = {"text": NO_DRAFT, "mode": "none"}
        check = None
    else:
        draft = draft_response(subject, body, evidence)
        check = check_draft(draft["text"], hits) if draft["mode"] != "none" else None
    draft_record = {**draft, **(check or {"citations": [], "citation_ok": False,
                                          "issues": ["No draft"]})}
    db.save_draft(conn, request_id, draft_record)
    db.log(conn, request_id, "drafted", {"mode": draft["mode"],
                                         "citations": draft_record["citations"],
                                         "issues": draft_record["issues"]})

    queue, reasons = route(classification, hits, retriever.min_evidence, check, injection, text)
    db.save_routing(conn, request_id, queue, reasons)
    db.log(conn, request_id, "routed", {"queue": queue, "reasons": reasons})

    checks = auto_send_checks(classification, hits, queue, draft_record, injection)
    if should_auto_send(checks):
        db.save_review(conn, request_id, "auto_send", AUTO_REVIEWER, draft_record["text"],
                       "All auto-send checks passed", None)
        db.log(conn, request_id, "auto_sent", {"checks": [name for name, _ in checks]})
    elif config.AUTO_SEND and draft_record["mode"] == "llm":  # say why an LLM reply wasn't auto-sent
        db.log(conn, request_id, "needs_person",
               {"failed": [name for name, ok in checks if not ok]})


def _route_after_error(conn: sqlite3.Connection, request_id: int, exc: Exception) -> None:
    """A step failed: record it and send the request to priority review with no draft."""
    conn.rollback()
    reason = f"Pipeline error: {type(exc).__name__}. Handle manually."
    db.log(conn, request_id, "pipeline_error", {"error": type(exc).__name__, "message": str(exc)[:200]})
    if not db.rows(conn, "SELECT 1 FROM classifications WHERE request_id=?", (request_id,)):
        db.save_classification(conn, request_id, {"category": "general", "urgency": "medium",
                                                  "risk": "high", "confidence": 0.0, "mode": "error"})
    db.save_draft(conn, request_id, {"text": NO_DRAFT, "mode": "none", "citations": [],
                                     "citation_ok": False, "issues": [reason]})
    db.save_routing(conn, request_id, "priority", [reason])
    db.log(conn, request_id, "routed", {"queue": "priority", "reasons": [reason]})


def submit_review(conn: sqlite3.Connection, request_id: int, action: str, reviewer: str,
                  final_text: str = "", reason: str = "", seconds_spent: float | None = None) -> dict:
    """Record a person's decision: approve, edit, reject or escalate."""
    if action not in {"approve", "edit", "reject", "escalate"}:
        raise ValueError(f"Unknown action: {action}")
    if action in {"reject", "escalate"} and not reason.strip():
        raise ValueError("A reason is required to reject or escalate")
    if not reviewer.strip():
        raise ValueError("Reviewer name is required")
    existing = db.rows(conn, "SELECT action FROM reviews WHERE request_id=?", (request_id,))
    if not existing:
        raise KeyError(request_id)
    if existing[0]["action"]:
        raise ValueError("This request has already been reviewed")
    db.save_review(conn, request_id, action, reviewer, final_text, reason, seconds_spent)
    db.log(conn, request_id, "reviewed", {"action": action, "reviewer": reviewer,
                                          "reason": reason, "seconds_spent": seconds_spent})
    return get_request(conn, request_id)


def get_request(conn: sqlite3.Connection, request_id: int) -> dict:
    """Everything known about one request, for the UI."""
    req = db.rows(conn, "SELECT * FROM requests WHERE id=?", (request_id,))
    if not req:
        raise KeyError(request_id)
    out = req[0]
    out["classification"] = (db.rows(conn, "SELECT * FROM classifications WHERE request_id=?",
                                     (request_id,)) or [None])[0]
    if out["classification"]:
        # The UI shows this flag instead of repeating the threshold, so the two can't disagree.
        out["classification"]["low_confidence"] = (
            out["classification"]["confidence"] < config.CONFIDENCE_THRESHOLD)
    out["evidence"] = db.rows(conn, "SELECT * FROM retrievals WHERE request_id=? ORDER BY rank",
                              (request_id,))
    d = (db.rows(conn, "SELECT * FROM drafts WHERE request_id=?", (request_id,)) or [None])[0]
    if d:
        d["citations"], d["issues"] = json.loads(d["citations"]), json.loads(d["issues"])
        d["citation_ok"] = bool(d["citation_ok"])
    out["draft"] = d
    r = (db.rows(conn, "SELECT * FROM reviews WHERE request_id=?", (request_id,)) or [None])[0]
    if r:
        r["routing_reasons"] = json.loads(r["routing_reasons"] or "[]")
    out["review"] = r
    reply = (r or {}).get("final_text") or (d["draft_text"] if d and d["mode"] != "none" else "")
    out["email"] = (compose_email(request_id, out["customer"], out["subject"], reply, out["evidence"])
                    if reply else None)
    out["audit"] = db.rows(conn, "SELECT * FROM audit_log WHERE request_id=? ORDER BY id",
                           (request_id,))
    for a in out["audit"]:
        a["details"] = json.loads(a["details"])
    return out
