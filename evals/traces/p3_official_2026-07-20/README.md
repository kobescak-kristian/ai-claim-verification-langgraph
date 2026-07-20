# P3 official run trace archive — 2026-07-20

Run: `p3-official-2026-07-20`, model `claude-sonnet-4-6`, LangSmith project
`ai-claim-verification-langgraph` (EU region). One JSON file per case,
each a full run tree — the parent LangGraph invocation plus every nested
child run (model calls and tool calls) — exported via
`langsmith.Client.read_run(run_id, load_child_runs=True)`.

Dashboard link, one representative case (labeled per its actual retention,
decisions/0003 Ruling 1):

- case_09_mixed_multi_claim_router: https://eu.smith.langchain.com/o/f34aeb42-2fb5-460e-8327-d41462a44412/projects/p/b5071ea3-1795-480f-b496-d30e8c3cf8e4/r/2ab7dee0-3801-40dc-a49f-dd7edbee7b28
  **Expires ~2026-08-03** (Developer-tier base retention is 14 days from
  the run date; after that window the link returns nothing in the UI or
  API — this is documented product behavior, not a guess).

## Evidentiary framing (decisions/0003 Ruling 1, binding)

This directory is the archive. The dashboard link above is a convenience
that goes dead in about two weeks; the committed JSON files are what
persists. This export is an **attested record produced by the repo
author** (this session, from the actual API responses at run time) — it
is not independently hosted or independently verifiable evidence. While
the LangSmith trace is still live (within its ~14-day window), a third
party can cross-check this export against the dashboard directly; after
that window, the committed JSON is the only surviving record, and its
authenticity rests on the repo's own git history rather than on external
corroboration. The P4 writeup states this plainly rather than presenting
the export as independently verifiable.

No feedback (scores, tags, corrections) was attached to any trace in this
project, by code or by hand, per decisions/0003 Ruling 3 — attaching
feedback to a base-tier trace silently upgrades its retention tier with a
billing impact, and that upgrade is explicitly out of scope.

## Files

| File | Case | Lines |
|---|---|---|
| case_01_supported_wireless_earbuds.json | 3 claims, all SUPPORTED | 17,272 |
| case_02_contradicted_price_laptop.json | 3 claims | 22,283 |
| case_03_contradicted_storage_phone.json | 3 claims | 17,259 |
| case_04_contradicted_release_date_camera.json | 3 claims | 17,259 |
| case_05_unverifiable_warranty_monitor.json | 3 claims | 19,893 |
| case_06_unverifiable_availability_speaker.json | 3 claims | 21,273 |
| case_07_adversarial_near_match_battery_earbuds.json | 2 claims | 14,870 |
| case_08_adversarial_rephrased_price_tablet.json | 2 claims | 14,870 |
| case_09_mixed_multi_claim_router.json | 4 claims, all 3 verdicts | 21,254 |
| case_10_supported_specs_bundle_keyboard.json | 4 claims | 21,254 |
| case_11_contradicted_availability_gpu.json | 3 claims | 22,283 |
| case_12_adversarial_authoritative_conflict_smartwatch.json | 2 claims | 14,870 |

Scored results, per-case cost/turns, and the gate verdict are in
`evals/parity_run_2026-07-20.md`, one level up — this directory holds the
raw trace export only.
