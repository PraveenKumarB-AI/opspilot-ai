"""SQLite storage. All SQL lives here so other modules never write queries directly."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opspilot import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer TEXT, channel TEXT, subject TEXT, body TEXT,
    received_at TEXT, status TEXT DEFAULT 'pending'
);
CREATE TABLE IF NOT EXISTS classifications (
    request_id INTEGER PRIMARY KEY, category TEXT, urgency TEXT, risk TEXT,
    confidence REAL, mode TEXT
);
CREATE TABLE IF NOT EXISTS retrievals (
    request_id INTEGER, rank INTEGER, chunk_id TEXT, doc_id TEXT, title TEXT,
    score REAL, text TEXT
);
CREATE TABLE IF NOT EXISTS drafts (
    request_id INTEGER PRIMARY KEY, draft_text TEXT, citations TEXT,
    citation_ok INTEGER, issues TEXT, mode TEXT
);
CREATE TABLE IF NOT EXISTS reviews (
    request_id INTEGER PRIMARY KEY, queue TEXT, routing_reasons TEXT,
    action TEXT, reviewer TEXT, final_text TEXT, reason TEXT,
    seconds_spent REAL, decided_at TEXT
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER, event TEXT,
    details TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS manual_timings (
    id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_ref TEXT, seconds REAL, created_at TEXT
);
CREATE TABLE IF NOT EXISTS eval_runs (
    run_id TEXT, metric TEXT, value REAL, notes TEXT, created_at TEXT
);
-- The audit log is append-only: block updates and deletes at the database level.
CREATE TRIGGER IF NOT EXISTS audit_no_update BEFORE UPDATE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
CREATE TRIGGER IF NOT EXISTS audit_no_delete BEFORE DELETE ON audit_log
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
-- INSERT OR REPLACE deletes the old row without firing DELETE triggers, so block it too.
CREATE TRIGGER IF NOT EXISTS audit_no_replace BEFORE INSERT ON audit_log
WHEN NEW.id IS NOT NULL AND EXISTS (SELECT 1 FROM audit_log WHERE id = NEW.id)
BEGIN SELECT RAISE(ABORT, 'audit_log is append-only'); END;
"""

REVIEW_STATUS = {"approve": "approved", "edit": "approved", "reject": "rejected",
                 "escalate": "escalated"}


def now() -> str:
    """Current UTC time as an ISO string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path | str | None = None) -> sqlite3.Connection:
    """Open the database, create tables if needed, and return rows as dicts."""
    conn = sqlite3.connect(str(path or config.DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def rows(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    """Run a SELECT and return a list of plain dicts."""
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def log(conn: sqlite3.Connection, request_id: int | None, event: str, details: dict) -> None:
    """Append one event to the audit log."""
    conn.execute(
        "INSERT INTO audit_log (request_id, event, details, created_at) VALUES (?,?,?,?)",
        (request_id, event, json.dumps(details), now()),
    )
    conn.commit()


def insert_request(conn, customer: str, channel: str, subject: str, body: str) -> int:
    cur = conn.execute(
        "INSERT INTO requests (customer, channel, subject, body, received_at) VALUES (?,?,?,?,?)",
        (customer, channel, subject, body, now()),
    )
    conn.commit()
    return int(cur.lastrowid)


def save_classification(conn, request_id: int, c: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO classifications VALUES (?,?,?,?,?,?)",
        (request_id, c["category"], c["urgency"], c["risk"], c["confidence"], c["mode"]),
    )
    conn.commit()


def save_retrievals(conn, request_id: int, hits: list[dict]) -> None:
    conn.executemany(
        "INSERT INTO retrievals VALUES (?,?,?,?,?,?,?)",
        [(request_id, i + 1, h["chunk_id"], h["doc_id"], h["title"], h["score"], h["text"])
         for i, h in enumerate(hits)],
    )
    conn.commit()


def save_draft(conn, request_id: int, d: dict) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO drafts VALUES (?,?,?,?,?,?)",
        (request_id, d["text"], json.dumps(d["citations"]), int(d["citation_ok"]),
         json.dumps(d["issues"]), d["mode"]),
    )
    conn.commit()


def save_routing(conn, request_id: int, queue: str, reasons: list[str]) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO reviews (request_id, queue, routing_reasons) VALUES (?,?,?)",
        (request_id, queue, json.dumps(reasons)),
    )
    conn.commit()


def save_review(conn, request_id: int, action: str, reviewer: str, final_text: str,
                reason: str, seconds_spent: float | None) -> None:
    """Record a reviewer's decision. Validates the action before writing anything."""
    if action not in REVIEW_STATUS:
        raise ValueError(f"Unknown review action: {action}")
    cur = conn.execute(
        "UPDATE reviews SET action=?, reviewer=?, final_text=?, reason=?, seconds_spent=?, "
        "decided_at=? WHERE request_id=? AND action IS NULL",
        (action, reviewer, final_text, reason, seconds_spent, now(), request_id),
    )
    # "AND action IS NULL" makes check-and-write one atomic step: if two reviews race,
    # only the first one updates the row; the second sees rowcount 0.
    if cur.rowcount == 0:
        conn.rollback()
        if rows(conn, "SELECT 1 FROM reviews WHERE request_id=?", (request_id,)):
            raise ValueError("This request has already been reviewed")
        raise LookupError(f"Request {request_id} has not been routed for review")
    conn.execute("UPDATE requests SET status=? WHERE id=?", (REVIEW_STATUS[action], request_id))
    conn.commit()
