"""Every request gets a professional draft; risky ones get a holding reply with no product facts."""
import pytest

from opspilot.holding import REPLIES, holding_kind
from opspilot.pipeline import process_request


def c(category="general", risk="low", urgency="medium"):
    return {"category": category, "risk": risk, "urgency": urgency, "confidence": 0.9}


@pytest.mark.parametrize("cls, text, injection, kind", [
    (c("billing", "high"), "I want a refund", True, "generic"),            # injection wins
    (c("security", "high"), "suspicious login", False, "security"),
    (c("data_privacy", "high"), "delete all our data", False, "data_privacy"),
    (c("billing", "high", "high"), "charged twice, urgent", False, "billing"),
    (c("tax", "high"), "tax filing deadline", False, "tax"),
    (c("access", "high", "high"), "the system is down", False, "outage"),
    (c("general", "high"), "contract dispute with your company over terms and penalties we were promised", False, "high_risk"),
    (c("general"), "it is not working", False, "unclear"),
    (c("general"), "do you offer the interface in french for our accounting team in our quebec office", False, "not_covered"),
])
def test_holding_kind(cls, text, injection, kind):
    assert holding_kind(cls, text, injection) == kind


def test_holding_replies_state_no_product_facts():
    for text in REPLIES.values():
        assert "[KB-" not in text and "$" not in text and "within" not in text  # no tags, amounts or deadlines


@pytest.mark.parametrize("subject, body", [
    ("Refund request", "We want a refund for the three days the system was down last month."),
    ("Delete our data", "Delete all our data and confirm when done."),
    ("Something broke", "Not working."),
    ("Dark mode", "Can we turn on dark mode in the interface?"),
])
def test_every_request_gets_a_draft_and_an_email_but_waits_for_a_person(conn, subject, body):
    r = process_request(conn, subject, body)
    assert r["draft"]["mode"] in ("holding", "llm", "fallback")
    assert r["email"] and r["email"]["body"].rstrip().endswith(f"Ticket #{r['id']}")
    assert r["status"] == "pending"   # holding replies are never auto-sent


def test_holding_email_reads_as_one_message(conn):
    r = process_request(conn, "Refund request", "We want a refund for the three days the system was down.")
    body = r["email"]["body"]
    assert body.count("Thank you") == 1                       # one thank-you, from the email opening
    assert "anything to add in the meantime" in body           # no "if this doesn't resolve" for a holding reply
    assert "doesn't resolve the issue" not in body
