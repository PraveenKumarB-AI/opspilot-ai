# Five-minute demo

**Before the call:** both servers running, `python -m eval.run_eval` done, at least three baseline
timings saved, other browser tabs closed. Tickets: T14 (routine), T33 (not covered), T36 (refund).

**1. The problem (New request page)**
"In support teams, most of the time on a ticket goes into finding the answer, not typing it. I built
a prototype to show how I'd speed that up without giving the model decisions it shouldn't make. The
data is invented, for a fictional asset-accounting product."

**2. A routine ticket (load T14 → Process → Open in review queue)**
"It classifies the ticket, runs hybrid search (keyword and vector search, merged), and drafts a
reply. Every sentence has a source tag, and the cited articles are highlighted here. A code check
confirms each tag points to something that was actually retrieved. Nothing risky, so it goes to
standard review, but a person still approves it." Approve.

**3. When it doesn't know (load T33 → Process)**
"This asks whether the product comes in French. The knowledge base doesn't cover that, so
confidence is low and the best source is weak. It writes no draft and sends it to a person, with the
reasons. I'd rather it say nothing than invent an answer."

**4. A risky ticket (load T36 → Process → Open in review queue)**
"This one asks for a refund. The routing rules send it to priority review and show why. Those rules
are plain code, not the model, so they're predictable and tested. The model can make a case
stricter, never looser." Escalate with "Refund: billing team".

**5. Evidence and how I built it (Dashboard → Audit trail)**
"On 52 synthetic tickets, every high-risk case was caught and every draft passed the citation check.
One out-of-scope question, T29, still gets through, and I kept it in the report rather than hide it."
On Audit, filter by T36's number: "Every step is logged, and the database rejects edits."
"I built it in modules with Claude Code, with a review after each module and a failing test before
each fix. With a real team I'd start by timing real tickets for a baseline and evaluating on their
past tickets before trusting any number."
