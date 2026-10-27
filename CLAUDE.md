# OpsPilot AI — project context for Claude Code

## What this is
Interview prototype: a support-ticket assistant that classifies requests, retrieves knowledge
with citations, drafts grounded replies, and routes risky or uncertain cases to human review.
Synthetic data only (fictional product "LedgerGrid"). Nothing here is PowerPlan data or results.

## Stack
Back end: Python 3.12, FastAPI (api/main.py), SQLite, TF-IDF + FAISS and rank_bm25 hybrid search,
optional Anthropic API with deterministic fallback, pytest + FastAPI TestClient.
Front end: React + Vite + Tailwind + Recharts in frontend/. The UI calls only the REST API
through src/api.js; no business logic in React.

## Rules
- Plan first: before editing, list the files you will change and why. Wait for approval.
- Small steps: one module per task. Short typed functions with docstrings.
- Business logic lives in opspilot/. api/main.py only validates input and calls it.
- Routing decisions are rule-based code in router.py, never decided by the LLM.
- Drafts may only use retrieved chunks; every factual sentence cites a tag like [KB-07 §2].
- The app and all tests must work with no API key (fallback mode, clearly labelled).
- Never hard-code or print secrets. Keys come from .env via python-dotenv.
- audit_log is insert-only.
- Every new function gets a pytest test. Run `pytest -q` after each change and report results.
- Never claim something works unless a test or a run shows it.

## Commands
- Back end: `source .venv/bin/activate && uvicorn api.main:app --reload` (http://localhost:8000/docs)
- Front end: `cd frontend && npm run dev` (http://localhost:5173)
- Tests: `pytest -q`
- Evaluation: `python -m eval.run_eval` (writes docs/eval_report.md)
