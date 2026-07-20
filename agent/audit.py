"""SQLite audit trail. Rows are written by the wrap_tool_call middleware
in agent/middleware.py, synchronously, before its result is returned
toward the model — audit-before-use is a property of that middleware's
call order, not of this module.

Shared across an eval run: each row is keyed by run_id (one per run
invocation) and case_id (the eval case that invocation was scoped to),
so a multi-case eval run can be queried per case from the one audit.db.
Schema mirrors the origin's tool_calls table (decisions/0002 Ruling 3)."""
import json
import sqlite3
from datetime import datetime, timezone

from .config import AUDIT_DB_PATH

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tool_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    case_id TEXT,
    tool_call_id TEXT,
    tool_name TEXT,
    event_type TEXT,
    timestamp TEXT,
    payload TEXT
)
"""

# Set via set_run_context() before each fresh agent invocation. Module-level
# state is safe here because invocations run sequentially, never concurrently
# (same rationale as the origin's agent/audit.py).
_current_run_id: str | None = None
_current_case_id: str | None = None


def set_run_context(run_id: str, case_id: str) -> None:
    global _current_run_id, _current_case_id
    _current_run_id = run_id
    _current_case_id = case_id


def init_audit_db() -> None:
    conn = sqlite3.connect(AUDIT_DB_PATH)
    try:
        conn.execute(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def write_audit_row(tool_call_id: str, tool_name: str, event_type: str, payload: dict) -> None:
    conn = sqlite3.connect(AUDIT_DB_PATH)
    try:
        conn.execute(
            "INSERT INTO tool_calls (run_id, case_id, tool_call_id, tool_name, "
            "event_type, timestamp, payload) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                _current_run_id,
                _current_case_id,
                tool_call_id,
                tool_name,
                event_type,
                datetime.now(timezone.utc).isoformat(),
                json.dumps(payload, default=str),
            ),
        )
        conn.commit()
    finally:
        conn.close()
