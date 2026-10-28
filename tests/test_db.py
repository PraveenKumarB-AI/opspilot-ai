import sqlite3

import pytest

from opspilot import db


def test_tables_are_created(conn):
    names = {r["name"] for r in db.rows(conn, "SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"requests", "classifications", "retrievals", "drafts", "reviews",
            "audit_log", "manual_timings", "eval_runs"} <= names


def test_insert_request_and_log(conn):
    rid = db.insert_request(conn, "Acme", "web", "Hello", "Body")
    db.log(conn, rid, "request_received", {"x": 1})
    assert db.rows(conn, "SELECT subject FROM requests WHERE id=?", (rid,))[0]["subject"] == "Hello"
    assert db.rows(conn, "SELECT event FROM audit_log")[0]["event"] == "request_received"


def test_audit_log_is_append_only(conn):
    db.log(conn, None, "test", {})
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("DELETE FROM audit_log")


def test_audit_log_rejects_update_and_replace(conn):
    db.log(conn, None, "original", {})
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("UPDATE audit_log SET event='tampered'")
    with pytest.raises(sqlite3.DatabaseError):
        conn.execute("INSERT OR REPLACE INTO audit_log (id, event) VALUES (1, 'tampered')")
    assert db.rows(conn, "SELECT event FROM audit_log")[0]["event"] == "original"


def test_unknown_review_action_writes_nothing(conn):
    rid = db.insert_request(conn, "Acme", "web", "Hello", "Body")
    db.save_routing(conn, rid, "standard", [])
    with pytest.raises(ValueError):
        db.save_review(conn, rid, "bogus", "Praveen", "text", "", 10)
    conn.commit()
    assert db.rows(conn, "SELECT action FROM reviews")[0]["action"] is None


def test_save_review_updates_both_tables(conn):
    rid = db.insert_request(conn, "Acme", "web", "Hello", "Body")
    db.save_routing(conn, rid, "standard", [])
    db.save_review(conn, rid, "approve", "Praveen", "Final reply", "", 42.5)
    review = db.rows(conn, "SELECT * FROM reviews WHERE request_id=?", (rid,))[0]
    assert review["action"] == "approve"
    assert review["reviewer"] == "Praveen"
    assert review["seconds_spent"] == 42.5
    assert db.rows(conn, "SELECT status FROM requests WHERE id=?", (rid,))[0]["status"] == "approved"


def test_save_review_requires_routing(conn):
    rid = db.insert_request(conn, "Acme", "web", "Hello", "Body")
    with pytest.raises(LookupError):
        db.save_review(conn, rid, "approve", "Praveen", "text", "", 10)
    assert db.rows(conn, "SELECT status FROM requests WHERE id=?", (rid,))[0]["status"] == "pending"


def test_second_review_cannot_overwrite_first(conn):
    # From the Module 8 review: check-then-write allowed a race; the write itself must refuse.
    rid = db.insert_request(conn, "Acme", "web", "Hello", "Body")
    db.save_routing(conn, rid, "standard", [])
    db.save_review(conn, rid, "approve", "Ana", "First", "", 10)
    with pytest.raises(ValueError):
        db.save_review(conn, rid, "reject", "Ben", "", "late click", 5)
    assert db.rows(conn, "SELECT reviewer FROM reviews")[0]["reviewer"] == "Ana"
