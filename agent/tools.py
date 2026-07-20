"""The 4 read-only tools available to the claim-verification agent, ported
from the origin's agent/tools.py. Faithful to the origin's signatures and
descriptions.

Read-only by construction: every tool either reads a local HTML file under
evals/dataset/ or appends to an in-memory findings list. None can write,
edit, execute shell commands, or reach beyond evals/dataset/.

The circuit breaker and budget ceiling that the origin checked inside each
tool function are NOT here — decisions/0002's amended cage split moves both
to the wrap_tool_call wrapper layer (agent/middleware.py), so they run
before any tool handler in this file is invoked at all."""
from langchain_core.tools import tool

from .pages import PathOutsideDatasetError, read_page

VALID_VERDICTS = {"SUPPORTED", "CONTRADICTED", "UNVERIFIABLE"}

# Populated by log_finding during a run; harness.py reads it after the graph
# invocation completes to build the verdict table. Reset by harness.py
# before each run (module-level state is safe: invocations run sequentially).
findings: list[dict] = []


def reset_run_state() -> None:
    """Call before each run: clears findings."""
    findings.clear()


@tool(
    "fetch_page",
    description=(
        "Fetch a local HTML page by path relative to evals/dataset/ (e.g. "
        "'case_01_supported_wireless_earbuds/target.html'). Returns the page "
        "title and its paragraphs. Rejects any path outside evals/dataset/."
    ),
)
def fetch_page(path: str) -> str:
    try:
        title, paragraphs = read_page(path)
    except (PathOutsideDatasetError, FileNotFoundError) as e:
        return f"ERROR: {e}"
    body = "\n".join(f"- {p}" for p in paragraphs)
    return f"# {title}\n\n{body}"


@tool(
    "extract_claims",
    description=(
        "Extract candidate factual claims from the target page (one per "
        "paragraph) given its path relative to evals/dataset/. Returns a "
        "numbered list; you decide which are claims worth verifying."
    ),
)
def extract_claims(path: str) -> str:
    try:
        _title, paragraphs = read_page(path)
    except (PathOutsideDatasetError, FileNotFoundError) as e:
        return f"ERROR: {e}"
    if not paragraphs:
        return "No paragraphs found on this page."
    numbered = "\n".join(f"{i + 1}. {p}" for i, p in enumerate(paragraphs))
    return f"Found {len(paragraphs)} candidate claim(s):\n{numbered}"


@tool(
    "compare_source",
    description=(
        "Fetch a source page (path relative to evals/dataset/) framed for "
        "comparison against a specific claim. Returns the source's full content "
        "so you can judge SUPPORTED / CONTRADICTED / UNVERIFIABLE yourself, per "
        "the comparison policy in your system prompt."
    ),
)
def compare_source(claim_text: str, source_path: str) -> str:
    try:
        title, paragraphs = read_page(source_path)
    except (PathOutsideDatasetError, FileNotFoundError) as e:
        return f"ERROR: {e}"
    body = "\n".join(f"- {p}" for p in paragraphs)
    return (
        f"Claim under review: \"{claim_text}\"\n"
        f"Source: {source_path} ({title})\n\n"
        f"Source content:\n{body}\n\n"
        "Decide whether this source SUPPORTS, CONTRADICTS, or does not "
        "address (UNVERIFIABLE) the claim, applying the comparison policy."
    )


@tool(
    "log_finding",
    description=(
        "Record the final verdict for one claim. verdict must be exactly one "
        "of SUPPORTED, CONTRADICTED, UNVERIFIABLE. evidence_source is the "
        "source path that determined the verdict, or 'none' if UNVERIFIABLE. "
        "Call this once per claim after you have finished investigating it."
    ),
)
def log_finding(claim_text: str, verdict: str, evidence_source: str, evidence_note: str) -> str:
    normalized = verdict.strip().upper()
    if normalized not in VALID_VERDICTS:
        return (
            f"ERROR: Invalid verdict '{verdict}'. Must be one of: "
            f"{', '.join(sorted(VALID_VERDICTS))}."
        )
    findings.append({
        "claim_text": claim_text,
        "verdict": normalized,
        "evidence_source": evidence_source,
        "evidence_note": evidence_note,
    })
    return f"Logged: {normalized} — {claim_text!r}"


ALL_TOOLS = [fetch_page, extract_claims, compare_source, log_finding]
