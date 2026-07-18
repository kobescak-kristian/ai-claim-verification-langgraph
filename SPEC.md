# SPEC — ai-claim-verification-langgraph

Classification: EXPERIMENT (framework port of an existing PROJECT).
Named reader: hiring managers evaluating agent-framework experience.
Trigger: agent-framework requirements (LangGraph/LangChain) recur across
current market job ads; decision dated 2026-07-18. Timebox: 2 weeks
part-time.

## What this is
A port of the existing bounded claim-verification agent
(ai-claim-verification-agent, hand-rolled on the Claude Agent SDK) to
LangGraph, facing the SAME frozen eval it already passed. One variable
changes: the framework. The deliverable is the port plus a comparison
writeup — what the framework gives, what it hides, what it cannot
enforce.

## What is ported
Same problem, same four read-only tools (fetch_page, extract_claims,
compare_source, log_finding), same verdict set
(SUPPORTED / CONTRADICTED / UNVERIFIABLE), same synthetic dataset
(12 cases / 35 claims), same comparison policy loaded at runtime from
the eval config. Agent built with `create_agent` (LangChain v1 /
LangGraph v1; `create_react_agent` is deprecated), dropping to a manual
StateGraph only if a cage property cannot be enforced through it.

## Cage translation (the four components)
1. Tool whitelist — the tools list passed at construction IS the
   whitelist; LangGraph agents have no built-in Write/Bash/Edit to
   disable. In-framework, but note: the property is weaker to
   demonstrate, not stronger to enforce.
2. Turn cap (20 model turns) — LangGraph's `recursion_limit` counts
   graph supersteps, not model turns (one turn ≈ agent step + tools
   step). Enforcement must cap model turns at exactly 20 and fail
   closed; representation (sized recursion_limit vs. turn counter in
   state) settled in Phase 1 and recorded in decisions/.
3. Budget ceiling + call-count circuit breaker — NOT framework
   primitives. Enforced inside the tool wrappers, same mechanism as the
   origin. Outside-framework by necessity; core writeup material.
4. Audit-before-use — SQLite audit row written synchronously inside
   each tool function before its result returns, porting the origin's
   proven pattern. Framework middleware/hooks may be evaluated in
   Phase 1 but are not trusted for the guarantee unless proven
   blocking; the bounds test enforces the property mechanically
   regardless of mechanism.
The full bounds-test suite is ported: same mechanical checks (path
escapes rejected and audited, answer-key leak markers absent, caps
enforced) against the LangGraph implementation.

## Eval wiring (LangSmith observes; the gate does not move)
- Eval files (dataset, ground truth, eval config, scorer) are read-only
  inputs copied verbatim from the origin repo. ZERO changes.
- Gate unchanged: precision >= 0.95 AND recall >= 0.90, positive class
  CONTRADICTED, same comparison policy. Scoring runs through the
  existing scorer against the frozen answer key. No LangSmith evaluator
  participates in pass/fail.
- LangSmith role: trace capture only, enabled via environment
  configuration on the free Developer tier (5,000 traces/month —
  a full eval run fits with a wide margin). Exact env-var names
  confirmed against live docs at Phase 1, not from memory.
- Data note: traces upload to a third-party cloud; dataset is synthetic
  by design, and the answer key never appears in any tool input or
  output (leak-marker test ported), so no key material can enter a
  trace.

## Eval parity (definition)
Identical inputs (12 cases / 35 claims), identical ground truth,
identical scorer and thresholds, identical eval model (Sonnet 4.6),
identical budget ceiling per task. Only the agent implementation
differs. The ported agent's official run is published PASS or FAIL as
scored — either result is the deliverable.

## Models & cost
Haiku 4.5 dev iterations, Sonnet 4.6 official run — matching the
origin. Difference from origin, stated plainly: LangGraph calls
Anthropic via API key (per-token billing), not Claude subscription
auth. Per-task ceilings reused: $0.25 dev / $1.50 eval.

## Phases & accept conditions
P0 Spec + ADR committed before any agent code (this commit).
P1 Scaffold — graph skeleton, 4 tools registered, cage implemented;
   ACCEPT: ported bounds suite green + one Haiku smoke case within caps.
P2 Port — full behavior; ACCEPT: three-verdict demo case correct on dev
   model within budget.
P3 Eval-parity run — official Sonnet run; ACCEPT: run completes within
   caps, result published honestly, LangSmith trace archived.
P4 Writeup — comparison doc (gives / hides / cannot enforce, per cage
   component); ACCEPT: README first screen states synthetic-data,
   pre-production status; writeup cross-linked from both repos; public
   flip executed at P4 accept.

## Out of scope
New domains, new evals, LangChain beyond the port's needs, paid
LangSmith tiers, live-web crawling, multi-agent variants.
