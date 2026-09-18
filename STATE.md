# STATE — ai-claim-verification-langgraph

**Classification:** EXPERIMENT (framework port of an existing PROJECT — `SPEC.md:1-6`). Per GOVERNANCE.md's Build-repo STATE rule clause 4, EXPERIMENT depth is a 5-line minimum, not a full page.

**RECONSTRUCTED** (clause 7): derived from the README's P0–P4 Version Log and `decisions/0001-0003` at scaffold time (2026-09-19, Q-72(f)), not written contemporaneously.

**Status:** P4 complete (2026-07-20) — official eval-parity run, precision 1.00 / recall 1.00, `decisions/0003`; comparison writeup (`COMPARISON.md`) published; repo flipped public per `decisions/0001`'s pre-registered "private at creation, flip at P4" rule. No production/deployment claim carried (README disclaimer).

**Since P4:** Q-48 pre-commit guard (`967236b`), backslash-path OS-parity fix (`333497c`), CI added (`02bfa10`), Apache-2.0 license (`8da0019`), Q-35 hook rollout — installed 2026-08-04 with the validator call deliberately left disabled (no validator file existed yet), AGENTS.md router adopted 2026-09-15/16 (`6301861`). Q-72(f) (this commit): STATE.md added; validator gains a STATE.md-existence check and the obsolete decision-cap removal; the stalled pre-push wiring is completed now that a truthful PASS is confirmed. Six-name BANNED_WITHOUT_TRIGGER propagation is SKIPPED — this repo carries a live root `SPEC.md` with no existing decision record citing it (checked directly against `decisions/*.md`); not fabricated to pass the check — named Q-72(f) residual.
