# 0002 — P1 technical rulings: turn cap, LangSmith config, audit mechanism

Date: 2026-07-20. Status: ACCEPTED.

## Ruling 1 — Turn cap: ModelCallLimitMiddleware, fail closed

Live docs (docs.langchain.com, reference.langchain.com, read 2026-07-20):
LangChain v1 ships `ModelCallLimitMiddleware` with a `run_limit`
(maximum model calls per single invocation) and
`exit_behavior="error"`, which raises `ModelCallLimitExceededError`
when the limit is exceeded. `recursion_limit` counts graph supersteps,
not model calls — the docs size it heuristically
(`2 * max_iterations + 1`), so it cannot cap model turns *exactly*.

Chosen mechanism:
- `ModelCallLimitMiddleware(run_limit=20, exit_behavior="error")` —
  exactly 20 model turns per run, fail closed, in-framework.
- `recursion_limit=43` set on invocation as a secondary fail-closed
  backstop (`GraphRecursionError` also raises); it should never fire
  before the middleware does.

Semantic mapping, recorded for the comparison writeup: the origin's
Agent SDK `max_turns=20` counts agent turns; `run_limit` counts model
calls per invocation. Closest available equivalent; treated as the
same bound for parity purposes.

## Ruling 2 — LangSmith configuration (EU region, tracing deferred)

Current variable names (langsmith SDK README / docs, read 2026-07-20):
`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_ENDPOINT`,
`LANGSMITH_PROJECT`. The legacy `LANGCHAIN_TRACING_V2` /
`LANGCHAIN_API_KEY` family is not used in this repo.

Account created 2026-07-20: EU region
(`eu.smith.langchain.com`), Developer tier (free, 5,000 traces/month —
a full eval run fits with wide margin). EU accounts authenticate only
against `https://eu.api.smith.langchain.com`; the SDK defaults to the
US endpoint, so `LANGSMITH_ENDPOINT` is mandatory in this setup.

`LANGSMITH_TRACING=false` through P1 and P2 (bounds suite and smoke
case run untraced). Tracing turns on at P3, where the accept condition
requires an archived trace. Per the eval-wiring contract (decision of
2026-07-18), LangSmith observes and never scores.

## Ruling 3 — Audit-before-use: wrap_tool_call middleware

Correction to the record, first: the spec's cage component 4 described
in-tool synchronous SQLite writes as "porting the origin's proven
pattern." Verified against the origin repo at public HEAD (2026-07-20):
the origin's tools contain no audit code; its audit rows are written by
an SDK hook (`PreToolUse`/`PostToolUse` in `agent/audit.py`), registered
in the harness — the audit sits *around* the tools, not inside them.
The in-tool write is the compliance orchestrator's mechanism, not the
origin's. The spec text stands as committed; this entry is the dated
correction.

Ruling: audit-before-use is implemented as a `wrap_tool_call`
middleware (LangChain v1 custom middleware, docs read 2026-07-20) —
the direct structural translation of the origin's SDK hooks. The
wrapper writes the pre-call audit row, invokes the tool handler,
writes the post-call row, and only then returns the result toward the
model. It is blocking by construction.

The 2026-07-18 spec pre-authorized exactly this evaluation: framework
hooks "are not trusted for the guarantee unless proven blocking."
Proof is mechanical, not documentary: the ported bounds suite asserts
through the middleware-wrapped execution path that an audit row exists
before any tool result is observable. If that test cannot be made
green, this ruling reverts to in-tool writes and the reversion is
recorded here.

Note for the writeup: the in-tool pattern remains the right call where
testability-first and a deterministic control plane dominate (as in
the orchestrator). It loses *here* because this repo's purpose is
framework fluency — the verdict is per repo purpose, not "middleware
is always better."

## Ruling 4 — Pre-registration scorecard (Decision 4, 2026-07-18)

The 2026-07-18 cage-translation contract claimed the framework offers
no primitive for budget ceiling, call-count circuit breaker, or
audit-before-use. Tested against live docs 2026-07-20:

- USD budget ceiling — HELD. No framework primitive; hand-built in
  the tool wrappers as registered.
- Call-count circuit breaker — FALSIFIED as stated:
  `ToolCallLimitMiddleware` exists (run/thread limits,
  `exit_behavior="error"`). The hand-built wrapper mechanism is
  retained as pre-registered; the primitive's existence is recorded
  here so the writeup argues from what the framework actually offers.
- Audit-before-use — FALSIFIED as stated: `wrap_tool_call` exists and
  is adopted per Ruling 3, under the spec's own proven-blocking
  clause.

Amended cage split, superseding the 2026-07-18 registration:
in-framework — whitelist-by-construction, turn cap (Ruling 1), audit
middleware (Ruling 3); hand-built in wrappers — USD budget ceiling,
call-count circuit breaker. One prediction held, two falsified, all
published: the writeup's evidence base is the tested record, not the
prediction.
