from opspilot import db, metrics
from opspilot.pipeline import process_request, submit_review


def test_no_time_saved_without_a_baseline(conn):
    r = process_request(conn, "Export", "How do I export a report to Excel?")
    submit_review(conn, r["id"], "approve", "Praveen", seconds_spent=60)
    m = metrics.summary(conn)
    assert m["avg_review_seconds"] == 60.0
    assert m["time_saved_pct"] is None


def test_time_saved_against_manual_baseline(conn):
    r = process_request(conn, "Export", "How do I export a report to Excel?")
    submit_review(conn, r["id"], "approve", "Praveen", seconds_spent=60)
    conn.execute("INSERT INTO manual_timings (ticket_ref, seconds, created_at) VALUES ('T02', 240, ?)",
                 (db.now(),))
    m = metrics.summary(conn)
    assert m["manual_baseline_seconds"] == 240.0
    assert m["time_saved_pct"] == 75.0
    assert m["approved_unedited_rate"] == 1.0


def test_rejected_reviews_do_not_count_as_handling_time(conn):
    a = process_request(conn, "Export", "How do I export a report to Excel?")
    b = process_request(conn, "Export", "How do I export a report to CSV?")
    submit_review(conn, a["id"], "approve", "Praveen", seconds_spent=60)
    submit_review(conn, b["id"], "reject", "Praveen", reason="wrong article", seconds_spent=5)
    assert metrics.summary(conn)["avg_review_seconds"] == 60.0
