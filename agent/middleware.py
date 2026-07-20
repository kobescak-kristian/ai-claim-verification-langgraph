"""Cage components enforced outside the framework's own primitives
(decisions/0002 Ruling 3 + Ruling 4 amended split):

- audit-before-use: SQLite pre/post row written around every tool call,
  blocking by construction — this uses the framework's `wrap_tool_call`
  hook as the injection point (a real primitive), but the guarantee is
  proven by the bounds suite, not assumed from the hook's existence.
- USD budget ceiling + call-count circuit breaker: no framework
  primitive is used for either (see decisions/0002 Ruling 4 — a
  call-count primitive, `ToolCallLimitMiddleware`, exists but the
  hand-built mechanism is retained as pre-registered). Tracked here and
  enforced before the tool handler runs, fail closed.

The turn cap (`ModelCallLimitMiddleware`) and the tool whitelist are
framework primitives wired in harness.py, not here.
"""
from langchain.agents.middleware import wrap_model_call, wrap_tool_call
from langchain_core.messages import ToolMessage

from .audit import write_audit_row
from .config import MAX_TOOL_CALLS, MODEL_PRICING_USD_PER_MTOK

_call_count = 0
_cost_usd = 0.0
_max_budget_usd = 0.0
_model_call_count = 0


def reset_wrapper_state(max_budget_usd: float) -> None:
    """Call before each run: clears the circuit-breaker counter, the model-
    call counter, and the cost accumulator, and sets this run's budget
    ceiling."""
    global _call_count, _cost_usd, _max_budget_usd, _model_call_count
    _call_count = 0
    _cost_usd = 0.0
    _max_budget_usd = max_budget_usd
    _model_call_count = 0


def current_cost_usd() -> float:
    return _cost_usd


def current_call_count() -> int:
    return _call_count


def current_model_call_count() -> int:
    return _model_call_count


@wrap_model_call
def track_cost(request, handler):
    """Accumulates USD cost from each model call's usage_metadata into the
    run-scoped budget counter that the circuit breaker below reads before
    serving the next tool call. Hand-built: LangChain has no per-run USD
    ceiling primitive (decisions/0002 Ruling 4)."""
    global _cost_usd, _model_call_count
    _model_call_count += 1
    response = handler(request)
    model_name = getattr(request.model, "model", None) or getattr(
        request.model, "model_name", None
    )
    pricing = MODEL_PRICING_USD_PER_MTOK.get(model_name)
    if pricing is not None:
        for message in response.result:
            usage = getattr(message, "usage_metadata", None)
            if not usage:
                continue
            _cost_usd += (
                usage.get("input_tokens", 0) * pricing["input"]
                + usage.get("output_tokens", 0) * pricing["output"]
            ) / 1_000_000
    return response


@wrap_tool_call
def audited_bounded_tool_call(request, handler):
    """Runs on every tool call, in this order:
    1. increment the circuit-breaker counter
    2. write the pre-call audit row (audit-before-use: this happens
       before the tool handler — or the denial path below — produces
       any result the model can see)
    3. if the call-count or budget ceiling is exceeded, fail closed:
       build the denial result WITHOUT invoking the real tool handler
    4. otherwise invoke the tool handler
    5. write the post-call audit row with whatever result was produced
    6. return that result toward the model
    """
    global _call_count
    _call_count += 1
    tool_call_id = request.tool_call["id"]
    tool_name = request.tool_call["name"]
    tool_args = request.tool_call.get("args", {})

    write_audit_row(tool_call_id, tool_name, "PreToolUse", {"tool_input": tool_args})

    if _call_count > MAX_TOOL_CALLS:
        result = ToolMessage(
            content=(
                f"Circuit breaker tripped: tool-call ceiling ({MAX_TOOL_CALLS}) "
                "reached for this run. No further tool calls will be served. "
                "Log findings for whatever claims you have already investigated "
                "and stop."
            ),
            tool_call_id=tool_call_id,
            status="error",
        )
    elif _cost_usd > _max_budget_usd:
        result = ToolMessage(
            content=(
                f"Budget ceiling tripped: run cost (${_cost_usd:.4f}) exceeds "
                f"the per-run ceiling (${_max_budget_usd:.2f}). No further tool "
                "calls will be served."
            ),
            tool_call_id=tool_call_id,
            status="error",
        )
    else:
        result = handler(request)

    response_content = result.content if isinstance(result, ToolMessage) else str(result)
    write_audit_row(
        tool_call_id,
        tool_name,
        "PostToolUse",
        {"tool_input": tool_args, "tool_response": response_content},
    )
    return result
