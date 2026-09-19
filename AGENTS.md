# AGENTS.md

Context router for coding agents working in this repository. It points to
the file that owns each topic. It does not restate current status, results
or configuration values; read the owning file instead.

## Repository purpose

ai-claim-verification-langgraph is a LangGraph / LangChain framework port
of a bounded claim-verification agent.

The purpose is not to invent a different claim-verification problem. The
problem, the tool set, the comparison policy and the evaluation are held
substantially fixed while the agent framework changes, so that framework
behaviour, the placement of enforcement and the resulting tradeoffs can be
compared against the hand-rolled origin implementation. The comparison is
the deliverable.

At runtime the system:

- receives one target page and that case's local source pages from the
  seeded dataset under `evals/dataset/`
- lets the model investigate the target page's factual claims through the
  registered tool list
- records one finding per claim — SUPPORTED, CONTRADICTED or UNVERIFIABLE
  — with an evidence source and a short note
- applies explicit execution bounds at both the framework layer and the
  wrapper layer while it does so
- writes every tool call to a local SQLite audit trail

Be precise about the tool surface. The list passed to `create_agent` in
`agent/harness.py` **is** the model-accessible whitelist; nothing else is
callable. This framework does not supply the origin harness's built-in
Write / Bash / Edit tool set, so there are no such built-ins here to
disable, and this implementation must never be described as disabling
them. Local writes made by the program — the audit database, and trace or
result exports produced by an explicitly invoked evaluation run — are
distinct from the model-accessible tool surface and are not actions the
model can choose.

## Authority and conflict handling

Each topic has one owning source:

| Source | Owns |
|---|---|
| `README.md` | Public description, usage, limitations, outcome summary and Version Log |
| `COMPARISON.md` | Framework-comparison conclusions and the interpretation of what the framework gives, hides and cannot enforce |
| `decisions/0001-port-target-and-parity-contract.md` | Original port target, the pre-registered cage-translation contract and the frozen eval-parity contract |
| `decisions/0002-p1-technical-rulings.md` | Accepted technical rulings that supersede parts of the original pre-registration where testing and documentation falsified it — in particular the turn-cap mechanism, the audit mechanism and the placement of the circuit breaker |
| `decisions/0003-p3-trace-archive-and-run-protocol.md` | Trace-archive semantics and the official-run protocol |
| `agent/harness.py` | Graph construction, the registered tool list, the model-call limit middleware, the recursion backstop and invocation behaviour |
| `agent/middleware.py` | Wrapper-layer cost tracking, the budget ceiling, the retained call-count circuit breaker and audit-before-use execution order |
| `agent/tools.py` | The actual claim-verification tools, verdict validation and the run's findings state |
| `agent/pages.py` | Dataset path containment and local HTML access |
| `agent/audit.py` | Local SQLite audit persistence |
| `agent/prompts.py` | System prompt construction and runtime loading of the comparison policy |
| `agent/config.py` | Current runtime constants: models, limits, pricing and tool names |
| `evals/eval_config.yaml` | The binding comparison policy, metric definitions and gate thresholds |
| `evals/ground_truth.json` | Frozen evaluation truth — never model evidence |
| `evals/run_parity.py` | The framework-native parity runner and its optional trace-export path |
| `evals/run_eval.py` | Frozen origin eval asset, retained for parity and reference |
| `evals/parity_run_*.md` and `evals/traces/` | Committed observed parity evidence and the trace archive |
| `tests/test_bounds.py` and `.github/workflows/ci.yml` | Mechanically asserted bounds and automated cross-platform verification |

When sources disagree:

- A later accepted decision record supersedes an earlier prediction where
  it explicitly records a tested correction.
- The accepted decision records define the experiment contract, and a later
  one may document corrections discovered during implementation.
- Source and config state current runtime behaviour.
- `evals/eval_config.yaml` and `evals/ground_truth.json` own the ruler.
- Committed run records state observations.
- Tests and CI state what is mechanically asserted.
- `COMPARISON.md` interprets the evidence; it does not override code or
  the frozen eval assets.
- Surface the disagreement rather than silently rewriting one side.
- If the requested work materially depends on an unresolved conflict, stop
  for owner review.

## Task routing

| Task | Go to |
|---|---|
| Experiment and port contract, scope, declared limits | `decisions/0001-port-target-and-parity-contract.md`, `decisions/0002-p1-technical-rulings.md` |
| Public description, usage, limitations, version history | `README.md` |
| Framework comparison: gives / hides / cannot enforce | `COMPARISON.md` |
| Port target and frozen parity contract | `decisions/0001-port-target-and-parity-contract.md` |
| Turn-cap, audit and cage technical rulings | `decisions/0002-p1-technical-rulings.md` |
| Tracing semantics and official-run protocol | `decisions/0003-p3-trace-archive-and-run-protocol.md` |
| Graph construction, registered tools, invocation | `agent/harness.py` |
| Cost tracking, budget ceiling, circuit breaker, audit middleware | `agent/middleware.py` |
| Tool behaviour, findings, verdict validation | `agent/tools.py` |
| Dataset path containment, local HTML reads | `agent/pages.py` |
| Audit persistence | `agent/audit.py` |
| Prompt construction and comparison-policy loading | `agent/prompts.py`, `evals/eval_config.yaml` |
| Runtime constants, model and provider settings | `agent/config.py` |
| Frozen evaluation policy, metrics, thresholds | `evals/eval_config.yaml` |
| Ground truth | `evals/ground_truth.json` |
| Seeded case pages | `evals/dataset/` |
| Parity runner and trace export | `evals/run_parity.py` |
| Retained origin eval asset | `evals/run_eval.py` |
| Recorded parity evidence and trace archive | `evals/parity_run_2026-07-20.md`, `evals/traces/` |
| Bounds regression tests | `tests/test_bounds.py` |
| Single-case live runner | `run_case.py` |
| Local setup and dependencies | `README.md` (Run It Yourself), `requirements.txt`, `.env.example` |
| CI | `.github/workflows/ci.yml` |
| Artifact validation | `.githooks/validate_artifacts.py` |
| Git guards | `.githooks/pre-commit`, `.githooks/pre-push` |

## Always-on constraints

1. **The registered tool list is the whitelist.** The tools passed to
   `create_agent` in `agent/harness.py` are the entire model-accessible
   tool surface. Do not claim this implementation disables an existing
   built-in Write / Bash / Edit set: unlike the origin SDK harness, this
   framework does not supply those capabilities automatically. Do not add
   state-changing, shell, publishing, sending, unrestricted file or
   network tools to that list as part of unrelated work.

2. **Framework bounds and hand-built bounds stay distinct.** The
   architecture splits the controls deliberately. Framework-side: the
   registered tool list, the model-call limit middleware, and the audit
   wrapper injection point. Hand-built in the wrapper layer
   (`agent/middleware.py`): USD cost accounting and the budget ceiling,
   and the retained call-count circuit breaker. Do not rewrite the
   comparison, the code or this router so that the framework appears to
   provide controls the implementation actually carries itself. Numeric
   limits live in `agent/config.py`; do not copy them into this file.

3. **A model-call limit is not a recursion limit.** The accepted design
   uses model-call limiting as the primary turn-like bound.
   `recursion_limit` is a secondary graph backstop and counts graph
   supersteps, not model calls. Do not replace the model-call mechanism
   with `recursion_limit` alone without an authorized architecture change.

4. **Audit-before-use stays blocking.** The `wrap_tool_call` middleware in
   `agent/middleware.py` writes the pre-call audit row before it invokes
   or denies the tool, and writes the post-call row before any result is
   returned toward the model. Denied calls are auditable too. Do not
   bypass that middleware path for model-accessible tool calls.

5. **Budget and call-count limits fail closed.** The wrapper layer checks
   the retained call-count circuit breaker and the tracked run budget
   before allowing a tool to execute. Do not convert either bound into
   warning-only behaviour, and do not move the economic ruler merely to
   let a run complete.

6. **Cost accounting is implementation logic.** Model-call usage is
   accumulated by the wrapper middleware using configuration owned in
   `agent/config.py`. Do not duplicate pricing values or model identifiers
   into this file. If provider pricing or model identifiers change, update
   the owning configuration and evidence under an authorized task rather
   than this router.

7. **Dataset path containment stays cross-platform.** Model-facing page
   tools remain constrained to `evals/dataset/` by `agent/pages.py`.
   Preserve rejection of parent traversal, absolute and drive-letter
   paths, and backslash-shaped escape forms on every operating system. Do
   not weaken containment for convenience.

8. **The verdict is model judgment.** The tools expose page content and
   record findings; they do not secretly compute semantic truth. The model
   applies the comparison policy and records exactly one of SUPPORTED,
   CONTRADICTED or UNVERIFIABLE. Any redesign that moves semantic judgment
   into deterministic tooling is a material behaviour change and needs its
   own authorization.

9. **The comparison policy has one runtime source.** It lives in
   `evals/eval_config.yaml` and is loaded into prompt construction at
   runtime by `agent/prompts.py`. Do not create a second mutable copy of
   it in this file or anywhere else.

10. **The frozen eval and parity ruler does not move to rescue a result.**
    The dataset, ground truth, metric definitions, thresholds and the
    scorer / parity contract are evaluation authority. Do not alter them
    after observing a result in order to manufacture parity or a PASS. A
    deliberate eval-policy change requires its own authorized task and
    must stay distinguishable from the run it evaluates.

11. **Ground truth is not model evidence.** Do not expose
    `evals/ground_truth.json`, its claim identifiers or equivalent
    answer-key data through prompts, tool inputs or tool responses. Keep
    the leakage regression checks in `tests/test_bounds.py`.

12. **Tracing is observability, not the gate.** Hosted tracing may observe
    explicitly authorized runs. It never determines PASS or FAIL and is
    not a substitute for the local safety audit trail. Routine development
    and verification must not turn tracing on, configure paid services, or
    upload data merely to run tests.

13. **Recorded runs and trace archives are evidence.** Do not rewrite
    committed parity results or trace archives to make later conclusions
    cleaner; the accepted run protocol publishes runs as scored. Do not
    attach hosted-tracing feedback under an unrelated task — the accepted
    decision record deliberately avoids feedback-driven retention and
    billing changes.

14. **Synthetic evidence stays bounded in what it claims.** Do not turn
    seeded synthetic-eval results or observed parity into claims of
    production deployment, live-web robustness or general framework
    superiority. Current evidence and limitations belong in `README.md`,
    `COMPARISON.md` and the committed eval records, not in this file.

15. **Local runtime and secret material stays local.** `.env`, the audit
    database, caches and virtual environments are gitignored and stay
    that way. No credentials and no machine-local absolute paths in
    tracked files. Trace and export files are committed only through an
    explicitly authorized evaluation or evidence task, never as incidental
    runtime output.

16. **No pushed-history rewrite.** Published evidence and comparison
    claims depend on stable commit history. Do not amend or rebase
    already-pushed commits, and do not force-push.

17. **Artifact rules.** Decision records have no hard maximum; write one
    only for a genuine material decision. Do not merge or delete existing
    records to satisfy a count. Version history stays in the README
    Version Log. If `.githooks/validate_artifacts.py` disagrees with
    current artifact policy, surface the disagreement rather than
    reshaping artifacts to satisfy the validator without an authorized
    validator task.

18. **This file is guidance, not enforcement.** Enforcement lives in the
    implementation, the middleware, the path checks, the tests, the git
    hooks and CI.

## Verification

Routine checks, neither of which needs an API key, a live model, hosted
tracing, `run_case.py` or `evals/run_parity.py`:

```bash
python .githooks/validate_artifacts.py .
python -m pytest tests/test_bounds.py -v
```

- The artifact validator must print `Tier 0: PASS`.
- The bounds suite exercises the real middleware-wrapped execution path.
  Some checks read the local audit database and skip when it holds no
  rows from a prior run; report skips honestly rather than fabricating
  rows. The suite may create or update that gitignored local database as
  a side effect of exercising the middleware — that is runtime test
  state, not a tracked artifact.
- `run_case.py` and `evals/run_parity.py` invoke a live model and spend
  money. They are not routine verification; run them only when a task
  explicitly calls for a live run, and do not enable tracing to satisfy a
  routine check.
- `.github/workflows/ci.yml` is the authoritative cross-platform routine
  run of the bounds suite. Its demo job stays dormant unless an API key
  secret is configured; do not add one as part of routine work.
