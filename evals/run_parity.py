#!/usr/bin/env python3
"""P3 eval-parity runner + LangSmith trace export (decisions/0003).

Distinct from the frozen evals/run_eval.py (the origin's Claude Agent SDK
runner, incompatible API, kept verbatim/untouched) — this is the
LangGraph-native equivalent used for this repo's P3 readiness check and
official run. Scoring logic mirrors the origin's run_eval.py exactly
(same matching rule, same metric definitions) for parity of method, not
of code path.

Tracing: .env keeps LANGSMITH_TRACING=false permanently. This script sets
it to "true" in THIS PROCESS'S environment only, for the run's duration;
never written back to .env, reverts naturally at process exit
(decisions/0003, sequencing section of the P3 dispatch).

No feedback is attached to any trace by this script (decisions/0003
Ruling 3).

Usage:
    python evals/run_parity.py --model haiku --case case_01_... --trace
    python evals/run_parity.py --model sonnet --all --trace \
        --export-traces evals/traces/p3_official_2026-07-20
"""
import argparse
import json
import os
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(REPO_ROOT / ".env")

import yaml  # noqa: E402

from agent.config import EVAL_MAX_BUDGET_USD, EVAL_MODEL, MAX_BUDGET_USD, MODEL  # noqa: E402
from agent.harness import build_agent, build_user_prompt  # noqa: E402
from agent.audit import init_audit_db, set_run_context  # noqa: E402
from agent import middleware as wrappers  # noqa: E402
from agent import tools as agent_tools  # noqa: E402
from langchain_core.messages import HumanMessage  # noqa: E402
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError  # noqa: E402
from langgraph.errors import GraphRecursionError  # noqa: E402
from agent.config import RECURSION_LIMIT  # noqa: E402

GROUND_TRUTH_PATH = REPO_ROOT / "evals" / "ground_truth.json"
EVAL_CONFIG_PATH = REPO_ROOT / "evals" / "eval_config.yaml"
UNRESOLVED = "UNRESOLVED"
POSITIVE_CLASS = "CONTRADICTED"


def match_predicted_verdict(claim_text, findings):
    """Same matching rule as the origin's run_eval.py: exact
    whitespace-stripped match, last call wins, UNRESOLVED if none."""
    match = None
    for f in findings:
        if f["claim_text"].strip() == claim_text.strip():
            match = f
    if match is None:
        return UNRESOLVED, None
    return match["verdict"], match["evidence_source"]


def load_gate_thresholds():
    with open(EVAL_CONFIG_PATH, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return {"precision_min": config["precision_min"], "recall_min": config["recall_min"]}


def compute_metrics(rows):
    thresholds = load_gate_thresholds()
    predicted_positive = [r for r in rows if r["predicted_verdict"] == POSITIVE_CLASS]
    true_positive = [r for r in predicted_positive if r["true_verdict"] == POSITIVE_CLASS]
    true_positive_total = [r for r in rows if r["true_verdict"] == POSITIVE_CLASS]
    precision = len(true_positive) / len(predicted_positive) if predicted_positive else 0.0
    recall = len(true_positive) / len(true_positive_total) if true_positive_total else 0.0
    gate_pass = precision >= thresholds["precision_min"] and recall >= thresholds["recall_min"]
    overall_correct = sum(1 for r in rows if r["match"])
    return {
        "positive_class": POSITIVE_CLASS,
        "precision": precision,
        "recall": recall,
        "precision_min": thresholds["precision_min"],
        "recall_min": thresholds["recall_min"],
        "gate": "PASS" if gate_pass else "FAIL",
        "overall_verdict_accuracy": overall_correct / len(rows) if rows else 0.0,
        "total_claims": len(rows),
        "predicted_contradicted_count": len(predicted_positive),
        "true_contradicted_count": len(true_positive_total),
        "true_positive_count": len(true_positive),
    }


def run_one_case(case, run_id, model, max_budget_usd, trace_run_id=None):
    """Fresh agent invocation for one case. If trace_run_id is given, that
    UUID becomes the LangSmith root run id for this invocation (so the
    trace can be looked up directly afterward, no search needed)."""
    case_id = case["case_id"]
    init_audit_db()
    set_run_context(run_id, case_id)
    agent_tools.reset_run_state()
    wrappers.reset_wrapper_state(max_budget_usd)
    agent = build_agent(model=model)
    prompt = build_user_prompt(case_id)

    config = {"recursion_limit": RECURSION_LIMIT}
    if trace_run_id is not None:
        config["run_id"] = trace_run_id
        config["run_name"] = f"parity-{case_id}"
        config["tags"] = ["p3-eval-parity", case_id]

    capped = False
    try:
        agent.invoke({"messages": [HumanMessage(content=prompt)]}, config=config)
    except (ModelCallLimitExceededError, GraphRecursionError):
        capped = True

    findings = list(agent_tools.findings)
    turns_used = wrappers.current_model_call_count()
    cost_usd = wrappers.current_cost_usd()

    claim_rows = []
    for claim in case["claims"]:
        predicted_verdict, predicted_source = match_predicted_verdict(claim["text"], findings)
        claim_rows.append({
            "claim_id": claim["id"],
            "claim_text": claim["text"],
            "true_verdict": claim["verdict"],
            "predicted_verdict": predicted_verdict,
            "predicted_source": predicted_source,
            "true_source": claim["evidence_source"],
            "match": predicted_verdict == claim["verdict"],
        })

    return {
        "case_id": case_id,
        "turns_used": turns_used,
        "cost_usd": cost_usd,
        "capped": capped,
        "claims": claim_rows,
        "case_pass": all(c["match"] for c in claim_rows),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["haiku", "sonnet"], required=True)
    parser.add_argument("--case", help="single case_id (readiness check)")
    parser.add_argument("--all", action="store_true", help="run all dev cases (official run)")
    parser.add_argument("--trace", action="store_true", help="enable LangSmith tracing for this run only")
    parser.add_argument("--export-traces", help="directory to export full run-tree JSON, one file per case")
    parser.add_argument("--run-id", default=None, help="run_id label for the audit trail")
    args = parser.parse_args()

    if args.trace:
        os.environ["LANGSMITH_TRACING"] = "true"

    model = MODEL if args.model == "haiku" else EVAL_MODEL
    max_budget_usd = MAX_BUDGET_USD if args.model == "haiku" else EVAL_MAX_BUDGET_USD

    with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
        ground_truth = json.load(f)

    if args.case:
        cases = [c for c in ground_truth["cases"] if c["case_id"] == args.case]
        if not cases:
            print(f"No such case: {args.case}", file=sys.stderr)
            sys.exit(1)
    elif args.all:
        cases = ground_truth["cases"]
    else:
        print("Specify --case <id> or --all", file=sys.stderr)
        sys.exit(1)

    run_id = args.run_id or f"parity-{args.model}-{uuid.uuid4().hex[:8]}"

    export_dir = None
    if args.export_traces:
        export_dir = REPO_ROOT / args.export_traces
        export_dir.mkdir(parents=True, exist_ok=True)

    client = None
    if args.trace:
        from langsmith import Client
        client = Client()

    case_results = []
    total_spend = 0.0
    trace_ids = {}

    for case in cases:
        trace_run_id = str(uuid.uuid4()) if args.trace else None
        print(f"Running {case['case_id']} (model={model}, trace={args.trace}) ...", file=sys.stderr)
        result = run_one_case(case, run_id, model, max_budget_usd, trace_run_id=trace_run_id)
        total_spend += result["cost_usd"]
        case_results.append(result)
        if trace_run_id:
            trace_ids[case["case_id"]] = trace_run_id
        print(
            f"  -> {result['case_id']}: cost ${result['cost_usd']:.4f}, "
            f"turns {result['turns_used']}, pass={result['case_pass']}",
            file=sys.stderr,
        )

    flat_rows = []
    for r in case_results:
        for c in r["claims"]:
            flat_rows.append({**c, "case_id": r["case_id"]})

    metrics = compute_metrics(flat_rows)

    output = {
        "run_id": run_id,
        "model": model,
        "total_spend": total_spend,
        "case_results": case_results,
        "metrics": metrics,
        "trace_ids": trace_ids,
    }
    print(json.dumps(output, indent=2))

    if client is not None and export_dir is not None:
        for case_id, trace_run_id in trace_ids.items():
            run = client.read_run(trace_run_id, load_child_runs=True)
            data = run.model_dump()
            out_path = export_dir / f"{case_id}.json"
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            print(f"Exported trace for {case_id} -> {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
