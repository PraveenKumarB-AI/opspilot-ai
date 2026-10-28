"""Dashboard numbers, computed from the database with SQL and Pandas."""
from __future__ import annotations

import sqlite3

import pandas as pd

from opspilot import db


def summary(conn: sqlite3.Connection) -> dict:
    """Counts, rates and timing. Time saved is shown only when a manual baseline exists."""
    df = pd.read_sql_query(
        "SELECT r.id, r.status, c.category, c.risk, v.queue, v.action, v.seconds_spent, d.mode "
        "FROM requests r LEFT JOIN classifications c ON c.request_id=r.id "
        "LEFT JOIN reviews v ON v.request_id=r.id LEFT JOIN drafts d ON d.request_id=r.id", conn)
    auto = df[df["action"] == "auto_send"]
    reviewed = df[df["action"].notna() & (df["action"] != "auto_send")]  # decisions made by people
    drafted = reviewed[reviewed["mode"].isin(["llm", "fallback"])]
    # Only approve/edit are comparable to handling a request by hand; reject/escalate are not.
    timed = reviewed[reviewed["action"].isin(["approve", "edit"])]["seconds_spent"].dropna()
    base = pd.read_sql_query("SELECT seconds FROM manual_timings", conn)["seconds"]
    ai_avg = float(timed.mean()) if len(timed) else None
    manual_avg = float(base.mean()) if len(base) else None
    saving = (round(100 * (manual_avg - ai_avg) / manual_avg, 1)
              if ai_avg is not None and manual_avg else None)
    return {
        "total_requests": int(len(df)),
        "auto_sent": int(len(auto)),
        "auto_send_rate": round(float(len(auto) / len(df)), 3) if len(df) else 0.0,
        "pending": int((df["status"] == "pending").sum()),
        "reviewed": int(len(reviewed)),
        "priority_rate": round(float((df["queue"] == "priority").mean()), 3) if len(df) else 0.0,
        "by_category": df["category"].fillna("unknown").value_counts().to_dict(),
        "by_queue": df["queue"].fillna("unknown").value_counts().to_dict(),
        "by_action": df["action"].dropna().value_counts().to_dict(),
        "approved_unedited_rate": (round(float((drafted["action"] == "approve").mean()), 3)
                                   if len(drafted) else None),
        "edit_rate": (round(float((drafted["action"] == "edit").mean()), 3)
                      if len(drafted) else None),
        "avg_review_seconds": round(ai_avg, 1) if ai_avg is not None else None,
        "manual_baseline_seconds": round(manual_avg, 1) if manual_avg is not None else None,
        "manual_samples": int(len(base)),
        "time_saved_pct": saving,
        "latest_eval": latest_eval(conn),
    }


def latest_eval(conn: sqlite3.Connection) -> dict | None:
    """Metrics from the most recent evaluation run, if any."""
    last = db.rows(conn, "SELECT run_id, created_at FROM eval_runs ORDER BY created_at DESC LIMIT 1")
    if not last:
        return None
    metrics = db.rows(conn, "SELECT metric, value FROM eval_runs WHERE run_id=?", (last[0]["run_id"],))
    return {"run_id": last[0]["run_id"], "created_at": last[0]["created_at"],
            "metrics": {m["metric"]: m["value"] for m in metrics}}
