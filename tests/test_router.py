from opspilot.router import route

LOW = {"category": "reporting", "risk": "low", "urgency": "low", "confidence": 0.95}
GOOD = [{"score": 0.5}]
OK_DRAFT = {"citation_ok": True, "issues": []}


def test_clean_case_goes_to_standard_review():
    assert route(LOW, GOOD, 0.2, OK_DRAFT, False, "how do I export")[0] == "standard"


def test_each_rule_triggers_priority():
    assert route({**LOW, "risk": "high"}, GOOD, 0.2, OK_DRAFT, False, "x")[0] == "priority"
    assert route({**LOW, "confidence": 0.5}, GOOD, 0.2, OK_DRAFT, False, "x")[0] == "priority"
    assert route(LOW, [{"score": 0.1}], 0.2, OK_DRAFT, False, "x")[0] == "priority"
    assert route(LOW, GOOD, 0.2, {"citation_ok": False, "issues": ["bad"]}, False, "x")[0] == "priority"
    assert route(LOW, GOOD, 0.2, OK_DRAFT, True, "x")[0] == "priority"
    assert route(LOW, GOOD, 0.2, OK_DRAFT, False, "this is unacceptable")[0] == "priority"


def test_evidence_uses_best_score_not_first():
    # From the Module 4 review: results are ordered by fused rank, so the first hit
    # is not always the strongest evidence. The router must use the maximum.
    hits = [{"score": 0.05}, {"score": 0.45}]
    queue, reasons = route(LOW, hits, 0.2, OK_DRAFT, False, "x")
    assert queue == "standard" and not any("Weak evidence" in r for r in reasons)


def test_confidence_exactly_at_threshold_is_not_low():
    # One keyword gives exactly 0.85; the rule is strictly "below 0.85".
    assert route({**LOW, "confidence": 0.85}, GOOD, 0.2, OK_DRAFT, False, "x")[0] == "standard"
