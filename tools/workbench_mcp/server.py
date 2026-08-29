"""MCP gateway over the Spec Workbench — read-only slice.

Scope of this slice: it answers "why is the specification like this" — which
accepted design decision owns a name, whether a gap belongs to a known closure
class, what the notes-language gate will say. There is no write tool and no
authoring action: designing states, editing notes, and exporting to the
factory remain explicit repository work on the canonical project branch.

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

Authority stays with the design-state documents; these tools project them. If
a tool and a document disagree, the document is right and the tool has a bug:
report the discrepancy instead of following the tool.
"""

mcp = FastMCP("spec-workbench", instructions=_INSTRUCTIONS)

_REPO_ROOT = authoring_pipeline.find_repo_root(Path(__file__).resolve().parent)

_ERRORS = (
    authoring_pipeline.AuthoringPipelineError,
    project_navigation.NavigationError,
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


if __name__ == "__main__":
    mcp.run()
