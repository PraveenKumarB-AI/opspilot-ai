"""Run all synthetic test requests through the pipeline and write docs/eval_report.md.

Usage:  python -m eval.run_eval
Results describe SYNTHETIC data only and are not business outcomes.
"""
from __future__ import annotations

import csv
import uuid
from datetime import datetime, timezone

from opspilot import config, db
from opspilot.pipeline import process_request
from opspilot.retriever import get_retriever

REPORT = config.ROOT / "docs" / "eval_report.md"


def pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 1) if d else None


def evaluate(save_to_db: bool = True) -> dict:
    """Return metrics and per-row results."""
    work = db.connect(":memory:")  # keep test requests out of the demo database
    with open(config.REQUESTS_CSV, newline="", encoding="utf-8") as f:
        cases = list(csv.DictReader(f))
    results = []
    for c in cases:
        r = process_request(work, c["subject"], c["body"], customer="Eval")
        top3 = [e["doc_id"] for e in r["evidence"][:3]]
        results.append({
            **c,
            "must_review": c["must_review"] == "True",
            "pred_category": r["classification"]["category"],
            "pred_risk": r["classification"]["risk"],
            "confidence": r["classification"]["confidence"],
            "queue": r["review"]["queue"],
            "reasons": r["review"]["routing_reasons"],
            "drafted": r["draft"]["mode"] in ("llm", "fallback"),
            "citation_ok": r["draft"]["citation_ok"],
            "doc_hit": bool(c["expected_doc"]) and c["expected_doc"] in top3,
        })
    labelled = [x for x in results if x["expected_category"] != "general"]
    with_doc = [x for x in results if x["expected_doc"]]
    high = [x for x in results if x["expected_risk"] == "high"]
    must = [x for x in results if x["must_review"]]
    clear = [x for x in results if not x["must_review"]]
    no_answer = [x for x in results if x["type"] in ("unsupported", "ambiguous")]
    drafted = [x for x in results if x["drafted"]]
    m = {
        "cases": len(results),
        "category_accuracy_pct": pct(sum(x["pred_category"] == x["expected_category"] for x in labelled), len(labelled)),
        "retrieval_hit_at_3_pct": pct(sum(x["doc_hit"] for x in with_doc), len(with_doc)),
        "citation_correct_pct": pct(sum(x["citation_ok"] for x in drafted), len(drafted)),
        "high_risk_recall_pct": pct(sum(x["pred_risk"] == "high" for x in high), len(high)),
        "must_review_recall_pct": pct(sum(x["queue"] == "priority" for x in must), len(must)),
        "unneeded_priority_pct": pct(sum(x["queue"] == "priority" for x in clear), len(clear)),
        "drafted_without_answer_pct": pct(sum(x["drafted"] for x in no_answer), len(no_answer)),
        "priority_review_rate_pct": pct(sum(x["queue"] == "priority" for x in results), len(results)),
    }
    run_id = uuid.uuid4().hex[:8]
    if save_to_db:
        conn = db.connect()
        now = db.now()
        conn.executemany("INSERT INTO eval_runs VALUES (?,?,?,?,?)",
                         [(run_id, k, v, "synthetic", now) for k, v in m.items() if v is not None])
        conn.commit()
    return {"run_id": run_id, "metrics": m, "results": results,
            "embeddings": get_retriever().embedder.backend, "llm": config.llm_enabled()}


def write_report(out: dict) -> None:
    m, res = out["metrics"], out["results"]
    misses = [x for x in res if (x["expected_category"] != "general" and x["pred_category"] != x["expected_category"])
              or (x["must_review"] and x["queue"] != "priority")
              or (not x["must_review"] and x["queue"] == "priority")
              or (x["expected_doc"] and not x["doc_hit"])]
    lines = [
        "# OpsPilot AI evaluation report", "",
        f"Run `{out['run_id']}` on {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC. "
        f"Embeddings: {out['embeddings']}. LLM: {'on' if out['llm'] else 'off (fallback mode)'}.", "",
        "> **All requests and documents are synthetic.** These numbers show how the prototype behaves "
        "on invented test data. They are not PowerPlan results or real business outcomes. The keyword "
        "fallback was written alongside this test set, so expect lower scores on real tickets.", "",
        "| Metric | Value | Target |", "| --- | --- | --- |",
        f"| Category accuracy (labelled cases) | {m['category_accuracy_pct']}% | track |",
        f"| Right document in top 3 | {m['retrieval_hit_at_3_pct']}% | high |",
        f"| Drafts passing citation check | {m['citation_correct_pct']}% | ~100% |",
        f"| High-risk recall | {m['high_risk_recall_pct']}% | 100% |",
        f"| Must-review cases sent to priority review | {m['must_review_recall_pct']}% | 100% |",
        f"| Clear cases sent to priority anyway | {m['unneeded_priority_pct']}% | low |",
        f"| Drafts written when no answer exists | {m['drafted_without_answer_pct']}% | 0% |",
        f"| Overall priority review rate | {m['priority_review_rate_pct']}% | track |", "",
        f"## Cases to look at ({len(misses)})", "",
        "| ID | Type | Expected | Got | Queue | Doc hit | Reasons |", "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for x in misses:
        lines.append(f"| {x['id']} | {x['type']} | {x['expected_category']} | {x['pred_category']} "
                     f"({x['confidence']}) | {x['queue']} | {'yes' if x['doc_hit'] else '-'} | "
                     f"{'; '.join(x['reasons']) or '-'} |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    result = evaluate()
    write_report(result)
    for k, v in result["metrics"].items():
        print(f"{k:32} {v}")
    print(f"\nReport written to {REPORT}")
