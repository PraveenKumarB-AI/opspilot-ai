"""Auto-send: safe cases go out without a person; anything risky or uncertain never does."""
import pytest

from opspilot import autosend, config, pipeline
from opspilot.pipeline import process_request, submit_review

SAFE_CLASS = {"category": "integration", "urgency": "medium", "risk": "low", "confidence": 0.97, "mode": "llm"}
STRONG = [{"score": 0.56}]
GOOD_DRAFT = {"mode": "llm", "citation_ok": True}


def _ok(**changes):
    c = {**SAFE_CLASS, **changes.pop("classification", {})}
    d = {**GOOD_DRAFT, **changes.pop("draft", {})}
    checks = autosend.auto_send_checks(c, changes.pop("hits", STRONG), changes.pop("queue", "standard"),
                                       d, changes.pop("injection", False))
    return autosend.should_auto_send(checks)


def test_safe_case_is_auto_sent():
    assert _ok()


@pytest.mark.parametrize("change", [
    {"queue": "priority"},
    {"injection": True},
    {"classification": {"risk": "high"}},
    {"classification": {"category": "billing"}},
    {"classification": {"category": "data_privacy"}},
    {"classification": {"category": "security"}},
    {"classification": {"confidence": 0.89}},
    {"hits": [{"score": 0.29}]},
    {"draft": {"mode": "fallback"}},
    {"draft": {"citation_ok": False}},
])
def test_any_failed_check_blocks_auto_send(change):
    assert not _ok(**change)


def test_switch_off_blocks_auto_send(monkeypatch):
    monkeypatch.setattr(config, "AUTO_SEND", False)
    assert not _ok()


def _fake_llm(monkeypatch, category="reporting", risk="low", confidence=0.97):
    """Pretend the LLM classified and drafted, so the pipeline can reach auto-send offline."""
    monkeypatch.setattr(pipeline, "classify", lambda text: {
        "category": category, "urgency": "medium", "risk": risk, "confidence": confidence, "mode": "llm"})

    def draft(subject, body, evidence):
        tag = f"[{evidence[0]['chunk_id']}]"
        return {"text": f"Open Reports and choose Export. {tag}", "mode": "llm"}
    monkeypatch.setattr(pipeline, "draft_response", draft)


def test_pipeline_auto_sends_and_logs_it(conn, monkeypatch):
    _fake_llm(monkeypatch)
    r = process_request(conn, "Export", "How do I export a report to CSV?", customer="Maria Lopez")
    assert r["status"] == "sent" and r["review"]["action"] == "auto_send"
    assert r["review"]["reviewer"] == pipeline.AUTO_REVIEWER
    assert "auto_sent" in [a["event"] for a in r["audit"]]
    assert r["email"]["body"].startswith("Hi Maria,") and "[KB-" not in r["email"]["body"]
    with pytest.raises(ValueError, match="already been reviewed"):
        submit_review(conn, r["id"], "approve", "Praveen", "x")


def test_pipeline_high_risk_waits_for_a_person(conn, monkeypatch):
    _fake_llm(monkeypatch, category="reporting", risk="high")
    r = process_request(conn, "Export", "How do I export a report to CSV?")
    assert r["status"] == "pending" and r["review"]["action"] is None
    failed = [a for a in r["audit"] if a["event"] == "needs_person"][0]["details"]["failed"]
    assert "Low risk" in failed


def test_metrics_count_auto_sent_separately(conn, monkeypatch):
    from opspilot import metrics
    _fake_llm(monkeypatch)
    process_request(conn, "Export", "How do I export a report to CSV?")
    m = metrics.summary(conn)
    assert m["auto_sent"] == 1 and m["auto_send_rate"] == 1.0
    assert m["reviewed"] == 0 and m["pending"] == 0      # people reviewed nothing; nothing waiting
    assert m["by_action"] == {"auto_send": 1}
