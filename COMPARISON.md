# Hand-rolled vs. framework: porting a bounded agent to LangGraph

One system, two implementations, one frozen exam. The original
claim-verification agent was hand-rolled on the Claude Agent SDK and
passed its eval gate at precision 1.00 / recall 1.00. This repo ports
it to LangGraph (LangChain v1, `create_agent`) and faces the same
frozen eval: identical dataset (12 cases / 35 claims), identical
ground truth, identical scorer and thresholds, identical eval model,
identical per-task budget ceiling. One variable changes: the
framework.

**Result: the port scored precision 1.00 / recall 1.00 — identical
to the origin (official run of 2026-07-20, $0.63 total; per-case
results in [`evals/parity_run_2026-07-20.md`](evals/parity_run_2026-07-20.md)).**

Parity at identical scores means the framework neither improved nor
degraded the outcome. That is the finding, not a disappointment: the
interesting differences are all in *enforcement* — what the framework
carries for you, what it hides from you, and what it cannot enforce
at all. This document walks those differences per safety component,
against predictions registered in `decisions/0001` **before** the
port was built, so the conclusions could not be retro-fitted to
whatever the port happened to do.

## The cage, component by component

The origin enforces five bounds ("the cage"): a tool whitelist, a
hard 20-model-turn cap, a per-run USD budget ceiling, a tool-call
circuit breaker, and audit-before-use (a SQLite audit row written
before any tool result reaches the model). The pre-registered
prediction (2026-07-18): whitelist and turn cap could live
in-framework; budget, circuit breaker, and audit could not,
"because the framework offers no primitive for them."

| Component | Predicted locus | Actual locus | Prediction |
|---|---|---|---|
| Tool whitelist | in-framework | in-framework | held |
| Turn cap (20, fail closed) | in-framework | in-framework (`ModelCallLimitMiddleware`) | held |
| USD budget ceiling | hand-built | hand-built (tool wrappers) | **held** |
| Call-count circuit breaker | hand-built | hand-built (kept per pre-registration) | **falsified** — `ToolCallLimitMiddleware` exists |
| Audit-before-use | hand-built | in-framework (`wrap_tool_call` middleware) | **falsified** — hooks exist, adopted |

One prediction held, two falsified. Both falsifications are
published rather than smoothed over — the point of pre-registering
was to find out, not to be right.

## What the framework gives

**An exact, fail-closed turn cap — but not where you'd first look.**
LangGraph's headline limit, `recursion_limit`, counts graph
supersteps, not model calls; it approximates turns rather than
counting them. The correct instrument is LangChain v1's
`ModelCallLimitMiddleware(run_limit=20, exit_behavior="error")`,
which caps model calls exactly and raises on breach. This port uses
the middleware as the cap and a sized `recursion_limit` as a
secondary backstop that should never fire first. One semantic note,
recorded in `decisions/0002`: the origin's cap counts agent turns
while `run_limit` counts model calls per invocation — the closest
available equivalent, treated as the same bound for parity purposes.

**A real hook layer.** `wrap_tool_call` middleware wraps every tool
execution: write the pre-call audit row, invoke the tool, write the
post-call row, return. It is blocking by construction — the direct
structural equivalent of the origin's SDK PreToolUse/PostToolUse
hooks, which is where the origin's audit actually lives (a detail
worth being precise about: the origin's audit sits *around* its
tools, not inside them). "Blocking by construction" was not taken on
faith: the ported bounds suite asserts, through the real
middleware-wrapped execution path, that an audit row exists before
any tool result is observable. The framework's claim was trusted
only after a mechanical test agreed.

**Observability for four environment variables.** With LangSmith
configured, every run emits a full run tree — model calls, tool
calls, token counts, latencies — with zero instrumentation code in
the agent. The origin's equivalent visibility is its hand-built
SQLite audit trail. The two are not substitutes: the audit trail is
the enforced safety record (local, tested, part of the cage), while
tracing is hosted diagnostics that never participates in pass/fail
here (rulings of 2026-07-20, `decisions/0003`). But as diagnostics,
the framework's version costs nothing to adopt and would take real
work to hand-roll.

**A whitelist by construction — with an asterisk.** The tools list
passed to `create_agent` *is* the whitelist; nothing else exists to
call. But this property is weaker to demonstrate than the origin's:
the Agent SDK ships built-in Write/Bash/Edit tools, so the origin's
four-tool whitelist visibly excludes capabilities the runtime
otherwise provides. LangGraph ships no built-in tools, so the same
property is enforced by default rather than by visible restriction.
Equally enforced, less legible as evidence.

**A call-count primitive this port deliberately does not use.**
`ToolCallLimitMiddleware` exists and falsifies the pre-registered
"no primitive" claim. The hand-built circuit breaker was kept
anyway, per the registration — but an honest comparison must record
that the framework offers one.

## What the framework hides

**The loop.** `create_agent` produces a working ReAct-style agent
whose control flow you never see. The origin's harness makes every
step explicit; here the graph is assembled for you. For shipping
speed this is a gift. For a system whose pitch is *provable* bounds,
it means every guarantee must be re-established from the outside —
by middleware you attach and tests you write — because you cannot
point at the loop and show where it stops.

**What its limits actually count.** The distance between
`recursion_limit` (supersteps) and "model turns" is exactly the kind
of gap that produces a cage that looks locked and is not. Getting
the cap right required reading current docs, not the framework's
most prominent knob.

**API surface churn.** `create_react_agent` is deprecated in the v1
line; one exception class this port needs
(`ModelCallLimitExceededError`) exists precisely as documented but
is not exported from the middleware package's public namespace and
must be imported from its defining module. Small things — but a
safety property that depends on catching an exception should not
require guessing where the exception lives.

## What the framework cannot enforce

**Money.** There is no USD budget primitive. The framework counts
calls and steps; dollars are a provider-side fact it never sees. The
per-run budget ceiling ($0.25 dev / $1.50 eval per task) is
hand-built in the tool-wrapper layer, fail closed, exactly as in the
origin. The billing models also differ, stated plainly: the origin
runs on Claude subscription auth, while this port calls Anthropic
via API key with per-token billing — so here the hand-built ceiling
is guarding a live meter, not an allowance. If your bound is
denominated in currency rather than counts, you are on your own —
in both worlds.

## Honest limits of this comparison

The eval runs on labeled synthetic pages by design; neither
implementation has operated in production. Parity was measured on
one task family, one dataset, one model pair — it is evidence the
port preserved the system's behavior under its gate, not a general
claim about either framework. The archived traces in
`evals/traces/` are an attested record committed by the repo author;
the corresponding LangSmith dashboard link is independently hosted
but expires ~14 days after the run under free-tier retention
(rulings of 2026-07-20, `decisions/0003`).

## What I'd tell you in an interview

The framework did not make the agent smaller — it made the
enforcement explicit. Measured on the agent layer alone
(`agent/*.py`, tests and eval assets excluded): 501 lines in the
origin, 577 in this port — 15% more. The files the framework was
supposed to slim did shrink: `audit.py` by 32 lines and `tools.py`
by 37, exactly where cage logic moved out of them. But that logic
landed in `middleware.py` — 129 lines with no origin equivalent —
together with the framework's own hook boilerplate, and the net is
growth. Meanwhile every safety property had to be re-proven against
a loop I didn't write, one limit that doesn't count what its name
suggests, and an API surface still settling. The bounds suite — not
the framework — is what makes the cage trustworthy in both
implementations. That is the durable lesson: frameworks relocate
enforcement; they don't remove the obligation to prove it — and
here, relocation cost lines rather than saving them.
