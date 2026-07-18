# 0001 — Port target, cage translation strategy, eval-parity contract

Date: 2026-07-18. Status: ACCEPTED.

## Decision 1 — Port target: ai-claim-verification-agent
Considered: claim-verification agent vs. compliance orchestrator.
Chosen: claim-verification agent. Reasons: (a) single-agent — a
multi-agent orchestrator port does not fit a 2-week part-time box;
(b) its frozen eval is green (precision 1.00 / recall 1.00, run
eval-05fbe4ee), so parity asks a falsifiable question: does the same
system hold the same gate under a different framework; (c) its 17-test
bounds suite is a ready-made translation checklist for the cage.

## Decision 2 — Repo name: ai-claim-verification-langgraph
Family prefix retained; sorts adjacent to the origin repo; the name
states the relationship. Final at creation per naming rule.

## Decision 3 — Private at creation, flip at P4
Repo is authored for the flip from the first commit: no internal
labels, rulings cited by date only, clean commit messages — the full
history becomes public unchanged. Flip executes when P4's accept
condition is met, so the repo lands public as a finished, gate-tested
artifact rather than a work surface.

## Decision 4 — Cage translation contract (pre-registered)
The four cage properties are requirements on the port, not suggestions:
whitelist-by-construction and a hard 20-model-turn cap in-framework
where the framework can carry them; budget ceiling, call-count circuit
breaker, and synchronous audit-before-use in the tool wrappers, because
the framework offers no primitive for them. Anything enforced outside
the framework is recorded as such — that record is the comparison
writeup's evidence base. Pre-registered so the writeup's conclusions
cannot be retro-fitted to whatever the port happened to do.

## Decision 5 — Eval-parity contract
Eval artifacts copied verbatim, read-only. Existing scorer and
thresholds decide PASS/FAIL. LangSmith observes and never scores.
Result published either way. Fail -> pass, if needed, must be the
ported system rising, never the ruler moving.
