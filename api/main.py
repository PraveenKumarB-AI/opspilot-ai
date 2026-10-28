"""OpsPilot AI REST API. The React front end calls only these endpoints."""
from __future__ import annotations

import csv
import sqlite3
from collections.abc import Iterator
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from opspilot import config, db, metrics
from opspilot.pipeline import get_request, process_request, submit_review
from opspilot.retriever import get_retriever

app = FastAPI(title="OpsPilot AI", version="1.0.0",
              description="Support-ticket assistant prototype. Synthetic data only.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])


def get_conn() -> Iterator[sqlite3.Connection]:
    """One database connection per HTTP request, closed afterwards.
    Sharing one connection across FastAPI's worker threads could mix transactions."""
    conn = db.connect()
    try:
        yield conn
    finally:
        conn.close()


class NewRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)
    customer: str = "Demo customer"
    channel: str = "web"


class Review(BaseModel):
    action: Literal["approve", "edit", "reject", "escalate"]
    reviewer: str = Field(min_length=1)
    final_text: str = ""
    reason: str = ""
    seconds_spent: float | None = Field(default=None, gt=0, lt=7200)


class Timing(BaseModel):
    ticket_ref: str = ""
    seconds: float = Field(gt=0, lt=7200)


@app.get("/health")
def health() -> dict:
    """Check the API is up and report which modes are active."""
    return {"status": "ok", "llm": config.llm_enabled(),
            "embeddings": get_retriever().embedder.backend}


@app.post("/requests")
def create_request(req: NewRequest, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    return process_request(conn, req.subject, req.body, req.customer, req.channel)


@app.get("/requests")
def list_requests(status: str | None = None, queue: str | None = None,
                  conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    sql = ("SELECT r.id, r.subject, r.customer, r.status, r.received_at, c.category, c.risk, "
           "c.urgency, c.confidence, v.queue FROM requests r "
           "LEFT JOIN classifications c ON c.request_id=r.id "
           "LEFT JOIN reviews v ON v.request_id=r.id WHERE 1=1")
    params: list = []
    if status:
        sql += " AND r.status=?"
        params.append(status)
    if queue:
        sql += " AND v.queue=?"
        params.append(queue)
    sql += " ORDER BY CASE v.queue WHEN 'priority' THEN 0 ELSE 1 END, r.id DESC"
    return db.rows(conn, sql, tuple(params))


@app.get("/requests/{request_id}")
def read_request(request_id: int, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    try:
        return get_request(conn, request_id)
    except KeyError:
        raise HTTPException(404, "Request not found")


@app.post("/requests/{request_id}/review")
def review(request_id: int, body: Review, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    try:
        return submit_review(conn, request_id, body.action, body.reviewer, body.final_text,
                             body.reason, body.seconds_spent)
    except LookupError:  # includes KeyError and 'not routed'
        raise HTTPException(404, "Request not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/metrics")
def get_metrics(conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    return metrics.summary(conn)


@app.get("/audit")
def audit(limit: int = Query(200, ge=1, le=1000), conn: sqlite3.Connection = Depends(get_conn)) -> list[dict]:
    return db.rows(conn, "SELECT * FROM audit_log ORDER BY id DESC LIMIT ?", (limit,))


@app.post("/baseline")
def add_timing(t: Timing, conn: sqlite3.Connection = Depends(get_conn)) -> dict:
    """Store one manual handling time (your stopwatch baseline)."""
    conn.execute("INSERT INTO manual_timings (ticket_ref, seconds, created_at) VALUES (?,?,?)",
                 (t.ticket_ref, t.seconds, db.now()))
    conn.commit()
    return {"ok": True}


@app.get("/samples")
def samples() -> list[dict]:
    """Synthetic example requests for the intake page."""
    with open(config.REQUESTS_CSV, newline="", encoding="utf-8") as f:
        return [{"id": r["id"], "type": r["type"], "subject": r["subject"], "body": r["body"]}
                for r in csv.DictReader(f)]
