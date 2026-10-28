from opspilot.classifier import classify_fallback


def test_clear_request_is_confident():
    c = classify_fallback("Our depreciation run failed with method missing")
    assert c["category"] == "depreciation"
    assert c["confidence"] >= 0.85
    assert c["risk"] == "low"


def test_refund_is_high_risk():
    assert classify_fallback("We want a refund for the outage")["risk"] == "high"


def test_routine_billing_question_is_low_risk():
    c = classify_fallback("How do we update the billing contact for invoices?")
    assert c["category"] == "billing"
    assert c["risk"] == "low"


def test_outage_and_mass_actions_are_high_risk():
    assert classify_fallback("LedgerGrid is down and we cannot log in")["risk"] == "high"
    assert classify_fallback("Reset every user's password")["risk"] == "high"


def test_vague_request_has_low_confidence():
    c = classify_fallback("Something broke after the update")
    assert c["category"] == "general" and c["confidence"] < 0.85


def test_downloaded_is_not_urgent():
    assert classify_fallback("The report never downloaded")["urgency"] != "high"


def test_system_down_is_urgent():
    assert classify_fallback("LedgerGrid is down for everyone")["urgency"] == "high"


def test_money_back_without_refund_word_is_high_risk():
    # Found in Claude Code review: no "refund"/"charged", but it is a money-back request.
    c = classify_fallback("We were billed twice for October. Please reverse the duplicate invoice.")
    assert c["category"] == "billing"
    assert c["risk"] == "high"
