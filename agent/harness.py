"""Bounded harness: wires the 4 tools (the tools list IS the whitelist —
LangGraph agents have no built-in Write/Bash/Edit to disable), the turn cap,
and the cage's wrapper-layer middleware into a single create_agent graph,
then runs one invocation against a single eval case.

ModelCallLimitExceededError is defined in a submodule of
langchain.agents.middleware and is not re-exported from the package's
__init__ (verified against the installed pin, decisions/0002)."""
import time

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain_core.messages import HumanMessage
from langgraph.errors import GraphRecursionError

from . import middleware as wrappers
from . import tools
from .audit import init_audit_db, set_run_context
from .config import (
    DATASET_ROOT,
    MAX_BUDGET_USD,
    MAX_TURNS,
    MODEL,
    RECURSION_LIMIT,
)
from .prompts import build_system_prompt


def build_agent(model: str = MODEL):
    return create_agent(
        model=model,
        tools=tools.ALL_TOOLS,  # this list IS the whitelist
        system_prompt=build_system_prompt(),
        middleware=[
            ModelCallLimitMiddleware(run_limit=MAX_TURNS, exit_behavior="error"),
            wrappers.track_cost,
            wrappers.audited_bounded_tool_call,
        ],
    )


def case_paths(case_id: str) -> tuple[str, list[str]]:
    """Return (target_rel_path, [source_rel_paths]) for a case, relative to
    evals/dataset/, discovered from the directory listing (not ground truth)."""
    case_dir = DATASET_ROOT / case_id
    if not case_dir.is_dir():
        raise FileNotFoundError(f"No such case under evals/dataset/: {case_id}")
    target = case_dir / "target.html"
    if not target.exists():
        raise FileNotFoundError(f"Case {case_id} has no target.html")
    sources = sorted(p.name for p in case_dir.glob("source_*.html"))
    return f"{case_id}/target.html", [f"{case_id}/{s}" for s in sources]


def build_user_prompt(case_id: str) -> str:
    target, sources = case_paths(case_id)
    source_lines = "\n".join(f"- {s}" for s in sources)
    return (
        f"Target page: {target}\n"
        f"Source pages:\n{source_lines}\n\n"
        "Verify every factual claim on the target page against the source "
        "pages, then log a finding for each claim."
    )


def format_report(
    case_id: str, findings: list[dict], turns_used: int, cost_usd: float, capped: bool
) -> str:
    lines = [f"Claim Verification Report — {case_id}", "=" * 64]
    for i, f in enumerate(findings, start=1):
        claim = f["claim_text"]
        if len(claim) > 55:
            claim = claim[:52] + "..."
        lines.append(f"{i} | {f['verdict']:<12} | {claim:<55} | {f['evidence_source']}")

    counts = {"SUPPORTED": 0, "CONTRADICTED": 0, "UNVERIFIABLE": 0}
    for f in findings:
        counts[f["verdict"]] += 1

    lines.append("")
    lines.append(
        f"Summary: {len(findings)} claim(s) verified "
        f"({counts['SUPPORTED']} SUPPORTED, {counts['CONTRADICTED']} CONTRADICTED, "
        f"{counts['UNVERIFIABLE']} UNVERIFIABLE)."
    )
    cap_note = " (turn cap reached)" if capped else ""
    lines.append(f"Run cost: ${cost_usd:.4f} | Turns used: {turns_used}/{MAX_TURNS}{cap_note}")
    return "\n".join(lines)


def run_case_result(
    case_id: str, run_id: str, model: str = MODEL, max_budget_usd: float = MAX_BUDGET_USD
) -> tuple[list[dict], int, float, bool]:
    """Fresh agent invocation scoped to one case: own graph (own turn cap),
    own circuit-breaker/budget counters, own findings list. Returns
    (findings, turns_used, cost_usd, capped) without formatting — callers
    build their own report from this."""
    init_audit_db()
    set_run_context(run_id, case_id)
    tools.reset_run_state()
    wrappers.reset_wrapper_state(max_budget_usd)
    agent = build_agent(model=model)
    prompt = build_user_prompt(case_id)

    capped = False
    try:
        agent.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"recursion_limit": RECURSION_LIMIT},
        )
    except (ModelCallLimitExceededError, GraphRecursionError):
        capped = True

    return (
        list(tools.findings),
        wrappers.current_model_call_count(),
        wrappers.current_cost_usd(),
        capped,
    )


def run_case(case_id: str) -> str:
    findings, turns_used, cost_usd, capped = run_case_result(
        case_id, run_id=f"single-{case_id}-{int(time.time())}"
    )
    return format_report(case_id, findings, turns_used, cost_usd, capped)
