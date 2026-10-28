"""The daily cap stops Claude calls on a public deployment; over the cap the app falls back."""
from opspilot import llm


def test_cap_allows_then_blocks(monkeypatch):
    monkeypatch.setenv("OPSPILOT_LLM_DAILY_CAP", "2")
    monkeypatch.setitem(llm._usage, "day", None)
    assert [llm._take_daily_slot() for _ in range(3)] == [True, True, False]


def test_no_cap_by_default(monkeypatch):
    monkeypatch.delenv("OPSPILOT_LLM_DAILY_CAP", raising=False)
    assert all(llm._take_daily_slot() for _ in range(50))
