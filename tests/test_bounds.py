"""Regression test for the bounds SPEC.md and decisions/ promise are
enforced in the harness, not just in documentation. Ported from the
origin's tests/test_bounds.py, adapted for the LangGraph cage
(decisions/0002):

(a) every path any tool call touched (per audit.db) resolves inside
    evals/dataset/, plus an explicit escape-attempt case asserting rejection
    at the path-resolver, and through fetch_page/compare_source exercised
    THROUGH THE REAL wrap_tool_call MIDDLEWARE (agent.middleware
    .audited_bounded_tool_call) — not the bare tool function. Calling a bare
    tool bypasses wrap_tool_call and proves nothing about audit-before-use
    (decisions/0002 Ruling 3's proven-blocking requirement).
(b) ground_truth.json content (the fixed eval target) never appears in any
    tool input or output the model saw — the agent must not be able to see
    the answer key it's being graded against.
(c) the call-count circuit breaker and USD budget ceiling (hand-built in
    the wrapper layer, decisions/0002 Ruling 4) trip and fail closed.
(d) audit-before-use: a pre-call row exists for every tool call BEFORE its
    result is observable, proven mechanically against a real run through
    the middleware-wrapped path.

Run:
    pytest tests/test_bounds.py -v
"""
import json
import sqlite3
import sys
import uuid
from pathlib import Path

import pytest
from langchain.agents.middleware import ToolCallRequest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from agent import middleware as wrappers  # noqa: E402
from agent import tools as agent_tools  # noqa: E402
from agent.audit import AUDIT_DB_PATH, init_audit_db, set_run_context  # noqa: E402
from agent.config import DATASET_ROOT, MAX_TOOL_CALLS  # noqa: E402
from agent.pages import PathOutsideDatasetError, resolve_dataset_path  # noqa: E402

GROUND_TRUTH_PATH = REPO_ROOT / "evals" / "ground_truth.json"

TOOLS_BY_NAME = {t.name: t for t in agent_tools.ALL_TOOLS}

ESCAPE_ATTEMPTS = [
    "../SPEC.md",
    "../../SPEC.md",
    "../../../etc/passwd",
    "..\\..\\SPEC.md",
    str(REPO_ROOT / "SPEC.md"),  # absolute path outside evals/dataset/
]


def _real_tool_handler(request: ToolCallRequest):
    """Invokes the actual registered tool, same as ToolNode would inside a
    real graph run — this is the `handler` the middleware wraps."""
    return request.tool.invoke(request.tool_call)


def call_through_middleware(tool_name: str, args: dict, run_id: str, case_id: str):
    """Exercises the real wrap_tool_call middleware (audited_bounded_tool_call)
    end to end: pre-audit row, the real tool handler, post-audit row. This is
    the middleware-wrapped execution path decisions/0002 Ruling 3 requires —
    NOT a bare call to the tool function."""
    set_run_context(run_id, case_id)
    tool_call = {
        "name": tool_name,
        "args": args,
        "id": f"test-{uuid.uuid4()}",
        "type": "tool_call",
    }
    request = ToolCallRequest(
        tool_call=tool_call, tool=TOOLS_BY_NAME[tool_name], state={}, runtime=None
    )
    return wrappers.audited_bounded_tool_call.wrap_tool_call(request, _real_tool_handler)


@pytest.fixture(autouse=True)
def _reset_state():
    init_audit_db()
    agent_tools.reset_run_state()
    wrappers.reset_wrapper_state(max_budget_usd=1.0)


# run_id used by this file's own adversarial (escape/circuit-breaker/budget)
# calls — excluded from the "historical" real-run check below, since those
# rows are deliberately invalid paths / tripped caps, not a well-behaved
# agent run. They ARE included in the ground-truth-leak check: that
# property must hold for adversarial calls too.
_BOUNDS_TEST_RUN_ID = "bounds-test"


def _audit_rows(*, exclude_bounds_test_rows: bool = False) -> list[sqlite3.Row]:
    if not AUDIT_DB_PATH.exists():
        pytest.skip(f"No audit.db at {AUDIT_DB_PATH} — run a case through harness.run_case first.")
    conn = sqlite3.connect(AUDIT_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        if exclude_bounds_test_rows:
            rows = conn.execute(
                "SELECT * FROM tool_calls WHERE run_id IS NULL OR run_id != ? ORDER BY id",
                (_BOUNDS_TEST_RUN_ID,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tool_calls ORDER BY id").fetchall()
    finally:
        conn.close()
    if not rows:
        pytest.skip("audit.db has no tool_calls rows.")
    return rows


def _iter_path_values(rows: list[sqlite3.Row]):
    for row in rows:
        payload = json.loads(row["payload"])
        tool_input = payload.get("tool_input") or {}
        for key in ("path", "source_path"):
            if key in tool_input:
                yield row["id"], tool_input[key]


class TestPathsStayInsideDataset:
    def test_every_audit_path_resolves_inside_dataset(self):
        """(a) Historical check: every path any tool call actually used, per
        the audit trail of a real run, resolves inside evals/dataset/."""
        rows = _audit_rows(exclude_bounds_test_rows=True)
        checked = 0
        for row_id, path_value in _iter_path_values(rows):
            checked += 1
            try:
                resolved = resolve_dataset_path(path_value)
            except PathOutsideDatasetError:
                pytest.fail(f"row {row_id}: path {path_value!r} resolved OUTSIDE evals/dataset/")
            except FileNotFoundError:
                pytest.fail(f"row {row_id}: path {path_value!r} does not exist under evals/dataset/")
            assert resolved.is_relative_to(DATASET_ROOT)
        assert checked > 0, "No path-bearing tool calls found in audit.db to verify against."

    @pytest.mark.parametrize("escape_path", ESCAPE_ATTEMPTS)
    def test_escape_attempt_rejected_by_resolver(self, escape_path):
        """(a) The path resolver itself must reject any path outside
        evals/dataset/, regardless of audit history."""
        with pytest.raises(PathOutsideDatasetError):
            resolve_dataset_path(escape_path)

    @pytest.mark.parametrize("escape_path", ESCAPE_ATTEMPTS)
    def test_escape_attempt_rejected_through_middleware_fetch_page(self, escape_path):
        """(a)+(d) Escape attempt exercised through the REAL wrap_tool_call
        middleware calling the actual fetch_page tool — proves the bound
        holds at the boundary the model actually calls, and that an audit
        row exists for the rejected attempt."""
        result = call_through_middleware(
            "fetch_page", {"path": escape_path}, run_id="bounds-test", case_id="escape-fetch"
        )
        assert result.status == "error" or "ERROR" in result.content
        assert "outside evals/dataset" in result.content or "rejected" in result.content.lower()

        conn = sqlite3.connect(AUDIT_DB_PATH)
        try:
            row = conn.execute(
                "SELECT * FROM tool_calls WHERE tool_call_id = ? AND event_type = 'PreToolUse'",
                (result.tool_call_id,),
            ).fetchone()
        finally:
            conn.close()
        assert row is not None, "No PreToolUse audit row found for the rejected call."

    @pytest.mark.parametrize("escape_path", ESCAPE_ATTEMPTS)
    def test_escape_attempt_rejected_through_middleware_compare_source(self, escape_path):
        """(a) Same, through compare_source — the second path-accepting tool."""
        result = call_through_middleware(
            "compare_source",
            {"claim_text": "irrelevant for this check", "source_path": escape_path},
            run_id="bounds-test",
            case_id="escape-compare",
        )
        assert result.status == "error" or "ERROR" in result.content
        assert "outside evals/dataset" in result.content or "rejected" in result.content.lower()


class TestAuditBeforeUse:
    def test_pre_row_exists_before_post_row_for_every_call(self):
        """(d) Mechanical proof of audit-before-use: for a real tool call run
        through the middleware, a PreToolUse row is written before the
        PostToolUse row — order asserted from the audit trail itself, not
        assumed from the middleware's source order."""
        result = call_through_middleware(
            "fetch_page",
            {"path": "case_01_supported_wireless_earbuds/target.html"},
            run_id="bounds-test",
            case_id="audit-order",
        )
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM tool_calls WHERE tool_call_id = ? ORDER BY id",
                (result.tool_call_id,),
            ).fetchall()
        finally:
            conn.close()
        assert [r["event_type"] for r in rows] == ["PreToolUse", "PostToolUse"]

    def test_denied_call_is_still_audited(self):
        """(d) Even a call denied by the circuit breaker gets a pre AND post
        audit row — the denial itself is observable in the audit trail, not
        silently dropped."""
        wrappers.reset_wrapper_state(max_budget_usd=1.0)
        wrappers._call_count = MAX_TOOL_CALLS  # force the next call to trip
        result = call_through_middleware(
            "fetch_page",
            {"path": "case_01_supported_wireless_earbuds/target.html"},
            run_id="bounds-test",
            case_id="audit-denial",
        )
        assert "Circuit breaker tripped" in result.content
        conn = sqlite3.connect(AUDIT_DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT * FROM tool_calls WHERE tool_call_id = ? ORDER BY id",
                (result.tool_call_id,),
            ).fetchall()
        finally:
            conn.close()
        assert [r["event_type"] for r in rows] == ["PreToolUse", "PostToolUse"]


class TestCapsEnforced:
    def test_circuit_breaker_trips_after_max_tool_calls(self):
        """(c) The call-count circuit breaker fails closed once MAX_TOOL_CALLS
        is exceeded, through the real middleware."""
        wrappers.reset_wrapper_state(max_budget_usd=1.0)
        last_result = None
        for _ in range(MAX_TOOL_CALLS + 1):
            last_result = call_through_middleware(
                "fetch_page",
                {"path": "case_01_supported_wireless_earbuds/target.html"},
                run_id="bounds-test",
                case_id="circuit-breaker",
            )
        assert "Circuit breaker tripped" in last_result.content

    def test_budget_ceiling_trips_when_cost_exceeds_ceiling(self):
        """(c) The USD budget ceiling fails closed once the tracked run cost
        exceeds the ceiling, through the real middleware."""
        wrappers.reset_wrapper_state(max_budget_usd=0.0001)
        wrappers._cost_usd = 1.0  # simulate cost already over the ceiling
        result = call_through_middleware(
            "fetch_page",
            {"path": "case_01_supported_wireless_earbuds/target.html"},
            run_id="bounds-test",
            case_id="budget-ceiling",
        )
        assert "Budget ceiling tripped" in result.content


class TestGroundTruthNotLeaked:
    def _ground_truth_secrets(self) -> set[str]:
        """Tokens that could only appear in a tool payload if ground_truth.json
        itself was read. Deliberately NOT the free-text evidence_note strings:
        those are natural-language descriptions of an objective fact, and a
        model reasoning correctly about the same evidence can converge on
        near-identical wording by coincidence. The claim `id` values are the
        reliable signal: they're constructed identifiers the model is never
        shown, so their presence in a tool payload is unambiguous proof of a
        leak, with no false-positive path via convergent reasoning."""
        with open(GROUND_TRUTH_PATH, encoding="utf-8") as f:
            gt = json.load(f)
        secrets = {"ground_truth.json", "ground_truth"}
        for case in gt["cases"]:
            for claim in case["claims"]:
                secrets.add(claim["id"])
        return secrets

    def test_ground_truth_never_appears_in_audit_payloads(self):
        """(b) The fixed eval target — the file itself, and its
        model-never-sees-these claim IDs — must never appear in any
        tool_input/tool_response the model saw."""
        rows = _audit_rows()
        secrets = self._ground_truth_secrets()
        for row in rows:
            payload_text = row["payload"]
            for secret in secrets:
                assert secret not in payload_text, (
                    f"row {row['id']}: ground_truth.json content leaked into "
                    f"audit payload: {secret!r}"
                )
