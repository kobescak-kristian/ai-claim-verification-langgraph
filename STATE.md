# STATE — ai-claim-verification-langgraph

**Classification:** EXPERIMENT (framework port of an existing PROJECT). An experiment carries a short state file by design, not a full page.

**RECONSTRUCTED:** this file was written after the fact, derived from the README's P0–P4 Version Log and `decisions/0001-0003`, not contemporaneously. Treat the commit history as authoritative where the two differ.

**Status:** P4 complete (2026-07-20) — official eval-parity run, precision 1.00 / recall 1.00, `decisions/0003`; comparison writeup (`COMPARISON.md`) published; repo flipped public per `decisions/0001`'s pre-registered "private at creation, flip at P4" rule. No production or deployment claim is carried (see the README disclaimer).

**Since P4:** pre-commit path guard (`967236b`); backslash-path OS-parity fix, which made the dataset-containment bound reject backslash-shaped paths on every OS (`333497c`); CI added (`02bfa10`); Apache-2.0 license (`8da0019`); git hooks installed with the artifact-validator call initially disabled, as no validator file existed yet (2026-08-04); `AGENTS.md` context router adopted (`6301861`); `STATE.md` added and the validator extended with a state-file check and the obsolete decision cap removed, completing the pre-push validator wiring (2026-09-19). The redundant root `SPEC.md` was retired in the same window rather than kept as a second contract: its substantive port and eval-parity contract lives in `decisions/0001`, with `decisions/0002` recording the corrections implementation falsified. The deleted file remains in git history (`f25a66d`).
