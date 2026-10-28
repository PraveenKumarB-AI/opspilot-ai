# OpsPilot AI

A support-ticket assistant that answers routine customer questions on its own, and hands anything
risky or uncertain to a person, with the reasons and a ready-to-send reply.

![A refund request routed to a person, with a professional holding reply and the email the customer will receive](docs/images/new-request.png)

I built this to work through a question that comes up whenever LLMs are used in customer support:
how do you get the speed of automatic replies without letting the model make decisions it shouldn't?

OpsPilot splits the work. The model reads tickets and writes drafts. Plain, tested code decides what
is risky, checks that every claim points to a real help article, and decides whether a reply can go
out on its own. The screenshot above shows a refund request: the rules flag it as high risk, so
instead of answering, OpsPilot drafts a holding reply that promises nothing about money and sends the
case to a person.

**Live demo:** https://opspilot-ai-ugnm.onrender.com
Free hosting, so the first visit after a quiet spell takes about a minute to wake up, and data resets
on restart. Drafts there are written by `openai/gpt-oss-120b` on Groq's free tier, capped at 200 calls
a day; after that it falls back to offline mode.

All data in this repo is synthetic. "LedgerGrid" is a made-up asset-accounting product, and its 14
help articles and 52 test tickets were written for this project. "PraveenPlan" is the made-up support
team that signs the emails. None of the numbers below are business results.

## What happens to a ticket

Every ticket gets a professional reply. What changes is who sends it.

| Ticket | Draft | Who sends it |
|---|---|---|
| Routine question with a strong, verified answer | An answer built only from the help articles, with a source on every sentence | **OpsPilot, automatically**, if all nine checks pass |
| Routine question that misses a check | The same kind of answer | A person approves or edits it |
| Refund, billing, data deletion, security, tax, outage | A **holding reply**: acknowledges the customer, says which team will handle it, asks for useful details, and states no product facts | A person, who can also escalate |
| Vague message ("it's not working") | A holding reply asking three short questions | A person |
| Question the help articles don't cover | A holding reply saying a specialist will answer | A person |
| Message that tries to give the assistant instructions | A neutral holding reply that ignores the instructions | A person |

## How it works

1. **Classify.** Category, urgency and risk, with a confidence score. With an API key an LLM does
   this (Claude, or any OpenAI-compatible API such as Groq); without one a keyword classifier runs.
   The LLM can raise a ticket's risk level but never lower it.
2. **Retrieve.** Hybrid search over the help articles: TF-IDF vectors in a FAISS index plus BM25,
   merged with reciprocal rank fusion. BM25 catches exact terms like error codes; the vectors catch
   paraphrases.
3. **Draft.** Safe tickets get an answer where every sentence ends with a source tag such as
   `[KB-07 §2]`. A guardrail checks in code that each tag points to a passage that was actually
   retrieved, and flags promises (refunds, dates, guarantees) with no source. Risky, vague and
   uncovered tickets get a holding reply instead.
4. **Route.** Seven rules choose between standard and priority review: possible prompt injection, high
   risk, low confidence (below 0.85), weak sources, failed citation check, urgency, and an upset
   customer. The reviewer sees exactly which rules fired.
5. **Auto-send or hand over.** A reply goes out with no person only if all nine checks pass (below).
   Otherwise it waits in the review queue. If a generated answer failed the citation check, Approve
   stays locked until the reviewer confirms they checked it against the sources.
6. **Email.** The customer receives a finished email: greeting by first name, the reply without
   source tags, the help articles it used, and a PraveenPlan Customer Support signature with the
   ticket number.
7. **Log.** Every step goes into an append-only audit table. SQLite triggers reject updates and
   deletes, so the history can't be rewritten.

If any step throws an error, the ticket isn't lost: it gets a holding reply, is logged, and goes to
priority review.

### The nine auto-send checks

All of them are plain code, so each one is tested and can be explained to a customer or an auditor.

1. Auto-send is switched on (`OPSPILOT_AUTO_SEND=off` turns it off)
2. All seven review rules are clear
3. No prompt injection
4. Low risk
5. Topic is not billing, data privacy, security, tax or general
6. Confidence of at least 0.90 (stricter than the 0.85 used for routing)
7. Strong source match (at least 0.30)
8. The reply was written by the LLM, not the offline fallback
9. The citation check passed

Every automatic send is logged with the checks it passed. When an LLM answer is held back, the
reviewer sees which checks it failed.

### What the customer receives

```
Subject: Re: ERP sync failures [Ticket #14]

Hi Maria,

Thank you for contacting PraveenPlan Support about "ERP sync failures".

Open Integration Hub > Sync Log to see failed records. The most common causes are a closed period
in the ERP, an inactive account code, or a missing cost center mapping. ...

For more detail, see these help articles:
- KB-07: ERP integration and sync errors

If this doesn't resolve the issue, simply reply to this email and a member of our team will follow up.

Best regards,
PraveenPlan Customer Support
Ticket #14
```

## Results

Evaluation on the 52 synthetic tickets, offline mode. Reproduce with `python -m eval.run_eval`.

| Metric | Result |
|---|---|
| High-risk tickets sent to priority review | 100% |
| Drafts passing the citation check | 100% |
| Must-review tickets sent to priority review | 96.7% |
| Correct article in the top 3 search results | 90.6% |
| Category accuracy | 88.9% |
| Answers drafted for questions the help articles can't answer | 13.3% |

In a dry run of the auto-send rules over the same tickets, 9 of the 22 routine questions qualified,
and none of the 30 high-risk, adversarial, vague or uncovered tickets did. With a live LLM the
confidence scores differ, so the exact count moves, but the risky groups are blocked by fixed rules.

Caveats: the keyword classifier was written alongside this test set, so these numbers are optimistic,
and real tickets will score lower. There is one known silent failure: T29, an out-of-scope question,
is classified confidently enough to reach standard review. I left it in rather than add a rule that
only exists to pass one test. Every miss is listed in [docs/eval_report.md](docs/eval_report.md).

## Screenshots

**Review queue.** Cases that need a person, priority first. The journey across the top shows each
stage the ticket went through and why it ended up here.

![Review queue](docs/images/review-queue.png)

**Dashboard.** Live counts, the share answered automatically, and the latest evaluation run. Review
time and time saved fill in once reviews and manual baseline timings exist.

![Dashboard](docs/images/dashboard.png)

**Audit trail.** Every step for every ticket, from intake to the final decision.

![Audit trail](docs/images/audit-trail.png)

## Running it locally

You need Python 3.12 and Node 20 or later.

```bash
git clone https://github.com/PraveenKumarB-AI/opspilot-ai.git
cd opspilot-ai
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt
pytest -q
python -m eval.run_eval
```

Run the app the way it's deployed, as one service:

```bash
cd frontend && npm install && npm run build && cd ..
uvicorn api.serve:app --port 8000
```

Open http://localhost:8000 and load a sample ticket on the New request page. The API docs are at
http://localhost:8000/api/docs. For front-end development with hot reload, run
`uvicorn api.main:app --reload` and, in a second terminal, `cd frontend && npm run dev`, then open
http://localhost:5173.

### Settings

It runs fully offline with no key. Copy `.env.example` to `.env` to change anything; `.env` is
git-ignored.

| Variable | What it does |
|---|---|
| `ANTHROPIC_API_KEY` | Use Claude for classification and drafting |
| `OPSPILOT_LLM_PROVIDER=openai` and `OPSPILOT_LLM_API_KEY` | Use any OpenAI-compatible API instead; Groq's free tier by default |
| `OPSPILOT_LLM_MODEL` / `OPSPILOT_LLM_BASE_URL` | Pick another model or provider |
| `OPSPILOT_LLM_DAILY_CAP` | Maximum LLM calls per day, for public demos; over the cap it falls back to offline mode |
| `OPSPILOT_AUTO_SEND=off` | Send every ticket to a person |

## Deploying

The `Dockerfile` builds the React app with Node, then serves it and the API from one Python process
running as a non-root user. It deploys as-is to Render's free tier: create a web service from this
repo, choose Docker, set the health check path to `/api/health`, and add the settings above as
environment variables. Use a separate API key with a spending limit for any public URL.

## Project layout

```
api/
  main.py        REST API (validation only; logic lives in opspilot/)
  serve.py       production entry point: API under /api plus the built React app
opspilot/
  classifier.py  category, urgency, risk and confidence
  retriever.py   hybrid search (FAISS + BM25 + reciprocal rank fusion)
  drafter.py     cited answers from retrieved passages
  holding.py     holding replies for risky, vague and uncovered tickets
  guardrails.py  citation check and prompt-injection detection
  router.py      the seven review rules
  autosend.py    the nine auto-send checks
  mailer.py      the customer email
  llm.py         Claude or OpenAI-compatible client, with a daily cap
  db.py, metrics.py
eval/            evaluation script (writes docs/eval_report.md)
tests/           pytest suite; runs offline, no API key needed
data/            synthetic help articles and test tickets
frontend/        React, Vite and Tailwind UI
docs/            user guide, demo script, evaluation report, development log
```

## How it was built

I built it module by module with Claude Code, using a `CLAUDE.md` for project rules and approving
every edit by hand. After each module I asked for a review, checked each finding myself, wrote a
failing test before fixing anything, and recorded the outcome in [docs/dev_log.md](docs/dev_log.md),
including the suggestions I rejected and why. One example: a draft that had failed the citation check
could still be approved in one click, so Approve now needs an explicit confirmation.

## Limits and next steps

- The test tickets are synthetic. The next step is to run the evaluation on a sample of a real team's
  resolved tickets and set the auto-send thresholds from that, one rule at a time.
- The manual baseline comes from one person's stopwatch. A real one would come from ticket
  timestamps across several agents.
- Search uses TF-IDF. Sentence embeddings would handle paraphrases better, with the evidence
  threshold re-tuned against the eval.
- "Send" records the decision; there is no email or ticketing integration yet.

## License

MIT. See [LICENSE](LICENSE).
