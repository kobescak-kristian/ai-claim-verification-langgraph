# 0003 — P3 rulings: trace archive definition, readiness check, run protocol clause

Date: 2026-07-20. Status: ACCEPTED.

## Ruling 1 — "Trace archived" means a committed export, not a link

Retention facts (docs.langchain.com usage-and-billing,
support.langchain.com, read 2026-07-20): Developer-tier traces are
base tier with 14-day retention; after the retention period, traces
are no longer accessible in the UI or API, and associated data is
deleted from internal systems within about a day. A dashboard share
link in the P4 writeup would therefore go dead roughly two weeks
after the official run. Doc conflict, recorded rather than silently
resolved: the official pricing page states extended retention as 180
days while the docs state 400 — irrelevant here (extended is paid,
out of scope per the 2026-07-18 spec), noted for accuracy.

Ruling: the P3 accept condition "LangSmith trace archived" is
satisfied by a JSON export of the official run's FULL RUN TREE
(parent run plus all nested child runs — model calls and tool calls),
committed to this repo as one file per case under a dated
evals/traces/ directory. A dashboard link may additionally be
included and must be labeled with its documented ~14-day expiry.
Screenshots are optional garnish, not the archive.

Evidentiary framing, binding on the P4 writeup: the committed export
is an attested record produced by the repo author, not independently
hosted evidence. The live LangSmith trace provides third-party
corroboration only during its 14-day window. The writeup states this
plainly and does not present the export as independently verifiable.

## Ruling 2 — P3-readiness check: traced dev-model case before the official run

Before any official-run spend, one Haiku case runs with tracing
enabled and the resulting trace is verified present via the LangSmith
API. This is a readiness check governing sequencing only — it is not
part of the P3 accept gate and its result moves no ruler. Purpose:
the failure mode "tracing misconfigured, discovered after the
official run" is eliminated for roughly $0.02. Trace volume is a
non-issue: a full eval run is trivial against the 5,000-trace monthly
allowance.

## Ruling 3 — No feedback attached to any trace in this project

The docs state that using certain features with base-tier traces
automatically upgrades their retention, with billing impact; attached
feedback is the documented trigger. Extended retention is paid and
out of scope. Rule: no feedback of any kind is attached to any trace
in this project, by code or by hand in the dashboard.

## Ruling 4 — Run-protocol clause (addition, not restatement)

The eval-parity contract of 2026-07-18 governs scoring and
publication unchanged; this file does not restate it. One clause is
added: every run executed under the official protocol is scored by
the existing scorer and published as scored, without exception. A
rerun motivated by trace-capture failure is still a full official
run — its score publishes alongside its predecessor's. "Capture
rerun" describes motive, never a scoring exemption. Pre-registered so
no later rerun can be framed as outside the published record.
