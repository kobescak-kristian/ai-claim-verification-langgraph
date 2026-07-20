from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATASET_ROOT = (REPO_ROOT / "evals" / "dataset").resolve()
EVAL_CONFIG_PATH = REPO_ROOT / "evals" / "eval_config.yaml"
AUDIT_DB_PATH = REPO_ROOT / "audit.db"

MODEL = "anthropic:claude-haiku-4-5-20251001"  # dev iterations (locked models decision, SPEC.md)
EVAL_MODEL = "anthropic:claude-sonnet-4-6"  # eval + demo runs (locked models decision, SPEC.md)

MAX_TURNS = 20  # ModelCallLimitMiddleware run_limit (decisions/0002 Ruling 1)
RECURSION_LIMIT = 43  # secondary fail-closed backstop on graph supersteps (2 * MAX_TURNS + 3)

MAX_BUDGET_USD = 0.25  # per-case ceiling for Haiku dev runs
EVAL_MAX_BUDGET_USD = 1.50  # per-case ceiling for Sonnet eval runs (higher token cost/turn)
MAX_TOOL_CALLS = 60  # circuit breaker: hard backstop independent of the turn cap

TOOL_NAMES = ["fetch_page", "extract_claims", "compare_source", "log_finding"]

# Per-MTok USD pricing for the wrapper-level budget ceiling (decisions/0002 Ruling 4:
# hand-built, no framework primitive). Source: platform.claude.com/docs pricing table,
# read 2026-07-20.
MODEL_PRICING_USD_PER_MTOK = {
    "claude-haiku-4-5-20251001": {"input": 1.0, "output": 5.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
}
