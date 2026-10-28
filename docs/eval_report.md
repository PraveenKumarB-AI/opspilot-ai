# OpsPilot AI evaluation report

Run `301de564` on 2026-10-28 03:59 UTC. Embeddings: tfidf. LLM: off (fallback mode).

> **All requests and documents are synthetic.** These numbers show how the prototype behaves on invented test data. They are not PowerPlan results or real business outcomes. The keyword fallback was written alongside this test set, so expect lower scores on real tickets.

| Metric | Value | Target |
| --- | --- | --- |
| Category accuracy (labelled cases) | 88.9% | track |
| Right document in top 3 | 90.6% | high |
| Drafts passing citation check | 100.0% | ~100% |
| High-risk recall | 100.0% | 100% |
| Must-review cases sent to priority review | 96.7% | 100% |
| Clear cases sent to priority anyway | 13.6% | low |
| Drafts written when no answer exists | 13.3% | 0% |
| Overall priority review rate | 61.5% | track |

## Cases to look at (9)

| ID | Type | Expected | Got | Queue | Doc hit | Reasons |
| --- | --- | --- | --- | --- | --- | --- |
| T16 | normal | tax | depreciation (0.425) | priority | yes | Low classification confidence (0.42 < 0.85) |
| T19 | normal | performance | reporting (0.425) | priority | yes | Low classification confidence (0.42 < 0.85) |
| T20 | normal | lease | lease (0.667) | priority | yes | Low classification confidence (0.67 < 0.85) |
| T29 | unsupported | general | unitization (0.85) | standard | - | - |
| T41 | high_risk | depreciation | depreciation (0.667) | priority | - | High-risk request (depreciation); Low classification confidence (0.67 < 0.85); Urgent request |
| T42 | high_risk | billing | general (0.3) | priority | yes | High-risk request (general); Low classification confidence (0.30 < 0.85); Weak evidence (best match 0.17 < 0.2) |
| T43 | high_risk | billing | billing (1.0) | priority | - | High-risk request (billing); Weak evidence (best match 0.00 < 0.2) |
| T44 | high_risk | access | access (0.85) | priority | - | High-risk request (access); Weak evidence (best match 0.15 < 0.2); Urgent request |
| T52 | normal | data_privacy | reporting (0.85) | standard | yes | - |
