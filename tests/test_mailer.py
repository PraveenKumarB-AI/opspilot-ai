"""The customer email is clean and professional; the tagged text stays internal."""
from opspilot.mailer import COMPANY, body_only, compose_email, greeting, strip_tags

EVIDENCE = [{"chunk_id": "KB-07 §2", "title": "ERP integration and sync errors: Sync errors"},
            {"chunk_id": "KB-07 §1", "title": "ERP integration and sync errors: Schedule"},
            {"chunk_id": "KB-02 §1", "title": "Exporting reports: Formats"}]


def test_tags_are_removed_cleanly():
    assert strip_tags("Open the Sync Log [KB-07 §2]. Then retry [KB-07 §1].") == "Open the Sync Log. Then retry."


def test_greeting_uses_real_first_name_only():
    assert greeting("maria lopez") == "Hi Maria,"
    assert greeting("Demo customer") == "Hello," and greeting("") == "Hello," and greeting("acme-123") == "Hello,"


def test_email_has_subject_articles_and_signature():
    e = compose_email(14, "Maria", "ERP sync failures", "Open the Sync Log. [KB-07 §2] Retry. [KB-07 §1]", EVIDENCE)
    assert e["subject"] == "Re: ERP sync failures [Ticket #14]"
    body = e["body"]
    assert body.startswith("Hi Maria,") and "[KB-" not in body
    assert body.count("KB-07: ERP integration and sync errors") == 1  # cited article listed once
    assert "KB-02" not in body                                          # not cited, not listed
    assert body.rstrip().endswith("Ticket #14") and f"{COMPANY} Customer Support" in body


def test_existing_greeting_and_signoff_are_not_doubled():
    draft = ("Hello,\n\nThanks for contacting us.\nOpen the Sync Log. [KB-07 §2]\n\n"
             "Let us know if this doesn't resolve it.\n\nBest regards,\nSupport team")
    assert body_only(strip_tags(draft)) == "Open the Sync Log."
    e = compose_email(3, "Demo customer", "Sync", draft, EVIDENCE)["body"]
    assert e.count("Best regards") == 1 and e.count("Hello,") == 1 and "Support team" not in e.replace("Customer Support", "")


def test_body_text_is_kept_when_it_only_looks_like_a_closer():
    assert body_only("Thanks to the new sync, records retry hourly.") == "Thanks to the new sync, records retry hourly."
