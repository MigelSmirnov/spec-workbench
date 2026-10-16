"""MCP gateway over the Spec Workbench — read-only slice.

Scope of this slice: it answers "why is the specification like this" — which
accepted design decision owns a name, whether a gap belongs to a known closure
class, what the notes-language gate will say — and gives a State 7 notes
writer the tools it asks while writing (tools/DATA_CLOSURE_WORKBENCH.md §4):
M1 resolve_data_address, M2 find_value_homes, M4 find_absence, M6
module_notes, and check_note_draft. There is no write tool and no authoring
action: designing states, editing notes, and exporting to the factory remain
explicit repository work on the canonical project branch.

Run (stdio transport):
    python tools/workbench_mcp/server.py

Register with Claude Code:
    claude mcp add workbench -- <spec-workbench>/tools/workbench_mcp/.venv/bin/python \\
        <spec-workbench>/tools/workbench_mcp/server.py
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

TOOLS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS_DIR))

from mcp.server.fastmcp import FastMCP

import authoring_pipeline
import project_navigation
from notes_workbench.factory_addresses import ResolverUnavailable
from spec_projection_workbench.model import SpecProjectionError
from workbench_mcp import service

_INSTRUCTIONS = """\
Read-only gateway over the Spec Workbench — the design corpus BEHIND the
factory's specifications. The factory MCP answers "what does the spec say and
which instrument may patch it"; this gateway answers "why does the spec say
that, and was it decided deliberately".

Position in the diagnostic chain: after the factory's spec_diagnostics has
named the addresses a change would touch, and BEFORE operations.json is
written, ask design_provenance for each touched name. A non-empty `decisions`
list or a waiver means the current shape is design intent with a recorded
reason: engage the decision (or its owner) in the change rationale, or stop
the change — do not patch it as if it were a bug.

Every answer is computed on a temporary read-only worktree of the project's
canonical ref, never on a working checkout: a dirty local branch does not
change these answers.

Writing a module's State 7 notes: a value with a home is written as its
address, a value without one stops the module with a structure request — never
as prose. Before writing a value, ask find_value_homes; before an address,
resolve_data_address; before stating "there is no home", find_absence (its
digests go into the request); before handing a note in, check_note_draft —
it applies the State 7 gate's checks of one note and the lint the writing
environment accepts notes by. module_notes gives the notes to rewrite.

Authority stays with the design-state documents; these tools project them. If
a tool and a document disagree, the document is right and the tool has a bug:
report the discrepancy instead of following the tool.
"""

mcp = FastMCP("spec-workbench", instructions=_INSTRUCTIONS)

_REPO_ROOT = authoring_pipeline.find_repo_root(Path(__file__).resolve().parent)

_ERRORS = (
    authoring_pipeline.AuthoringPipelineError,
    project_navigation.NavigationError,
    ResolverUnavailable,
    SpecProjectionError,
    OSError,
    ValueError,
)


def _known_cases() -> list[str]:
    try:
        return [row["id"] for row in service.list_cases(_REPO_ROOT)["cases"]]
    except _ERRORS:
        return []


@mcp.tool()
def list_workbench_cases() -> dict[str, Any]:
    """Curated workbench projects with canonical refs, current stage, and the
    factory project each case targets (from 90_factory_target.json).

    Use this first to translate a factory project name (e.g. "Cabinet_web")
    into its workbench case (e.g. "cabinet-web-backend").
    """
    try:
        return service.list_cases(_REPO_ROOT)
    except _ERRORS as exc:
        return {"error": str(exc)}


@mcp.tool()
def workbench_state(project: str) -> dict[str, Any]:
    """Current authoring state of one workbench case: canonical ref, the first
    not-ready design phase, and why it is not ready.

    The returned action's shell command is withheld deliberately: it assumes a
    materialized checkout this gateway owns. Authoring remains explicit
    repository work on the canonical project branch.
    """
    try:
        return authoring_pipeline.project_next(_REPO_ROOT, project)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def design_provenance(project: str, name: str) -> dict[str, Any]:
    """Where one name came from: the accepted design decisions that own or
    consume it (with their authored body), its State 6 surface entry, trace
    ownership, closure-gap waivers touching it, and the notes scoped to it.

    Call this for every name a contemplated spec change would touch. When
    `deliberate_design_signals` is true, the current shape was decided on
    purpose: the change rationale must engage those decisions, or the change
    should stop.
    """
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.provenance(case_root, name)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def closure_diagnostics(project: str) -> dict[str, Any]:
    """Closure-gap fuses over the assembled case — gap classes, not symptoms —
    split into open findings and deliberately waived ones (with reasons), plus
    the State 6 contract warnings.

    A waived finding is a recorded decision: treat it as design intent. An open
    finding names the defect class; the fix belongs at the class level.
    """
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.closure(case_root)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def notes_language(project: str, scope: str | None = None) -> dict[str, Any]:
    """The notes-language findings the factory's pre-generation gate will apply,
    computed against the same assembled specification, before export.

    Pass `scope` (a function or module name) to filter findings to one name.
    """
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.notes_language(case_root, scope)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def design_context(project: str, location: str, radius: int = 6) -> dict[str, Any]:
    """Authored design text around one PATH:LINE location (as returned by
    design_provenance), with the indexed item that owns the line.

    This is the bounded reader for design documents: prefer it over asking for
    whole files.
    """
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.design_context(case_root, location, radius)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def resolve_data_address(project: str, address: str) -> dict[str, Any]:
    """M1: whether one data address, written as in a note (`= models.X`,
    `= rules.…`, `= config.…`, `the imported X constant`), is a legal node —
    the Factory resolver's verdict (status legal / unresolved / illegal, code,
    message; for a legal node its kind, canonical JSON and sha256)."""
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.resolve_address(case_root, address)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def find_value_homes(project: str, value: str) -> dict[str, Any]:
    """M2: where a literal (`30`, `"21.00"`, `personal_data`) is declared.
    `homes_reaching_code` are the homes a note may name instead of the
    literal; none means the value has no home: stop with a structure request."""
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.value_homes(case_root, value)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def find_absence(project: str, terms: list[str]) -> dict[str, Any]:
    """M4: where each term (`timeout`, `retry`, `ceiling`) occurs as a key or
    value in models / config / rules / contracts, and the sha256 of each
    namespace looked through — the `absence` a structure request must carry."""
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.absence(case_root, terms)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def module_notes(project: str, module: str) -> dict[str, Any]:
    """M6: the callables of one module and its authored notes (path, line,
    scope, class, text) — the notes to rewrite, not to add beside."""
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.module_notes(case_root, module)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


@mcp.tool()
def check_note_draft(project: str, note: str) -> dict[str, Any]:
    """M3 with verdicts: one draft note `<scope>: [CLASS] prose` through the
    State 7 gate's checks of one note (scope, class, stub, references; from
    standard_version 3 the Factory's resolver, L1) and the writing
    environment's lint — L2 literal with a home, L3 uncovered data signal,
    L4 restated enumeration, L5 prose shared with another module. `clean` is
    false while any finding blocks. Whether every callable has a positive
    note is a property of the whole module, checked when notes are accepted."""
    try:
        with authoring_pipeline.materialized_project(_REPO_ROOT, project) as (_, case_root):
            return service.check_note_draft(case_root, note)
    except _ERRORS as exc:
        return {"error": str(exc), "known_cases": _known_cases()}


if __name__ == "__main__":
    mcp.run()
