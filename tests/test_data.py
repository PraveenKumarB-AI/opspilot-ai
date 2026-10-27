import csv

from opspilot import config

TYPES = {"normal", "ambiguous", "unsupported", "high_risk", "adversarial"}


def test_knowledge_files_have_sections():
    files = sorted(config.KNOWLEDGE_DIR.glob("KB-*.md"))
    assert len(files) == 14
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert text.startswith("# "), f.name
        assert text.count("\n## ") >= 2, f.name


def test_requests_csv_is_labelled():
    with open(config.REQUESTS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 52
    assert {r["type"] for r in rows} == TYPES
    assert len({r["id"] for r in rows}) == 52
    for r in rows:
        assert r["must_review"] in ("True", "False")
        if r["expected_doc"]:
            assert any(config.KNOWLEDGE_DIR.glob(f"{r['expected_doc']}_*.md")), r["id"]
