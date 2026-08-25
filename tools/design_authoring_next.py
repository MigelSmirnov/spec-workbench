#!/usr/bin/env python3
"""Generic deterministic authoring sequencer for one materialized project case.

This module is the pipeline API. The repository-level ``tools/authoring.py`` CLI
resolves a logical project/ref and calls ``next_step`` on a temporary worktree.
Future MCP transport must call the same API rather than reimplementing routing.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import design_lint
import design_router_context
import design_stage3
import design_stage4
import design_stage5
import design_stage6_contracts
import design_stage6_data
import design_trace
from notes_workbench import gate as notes_gate
from persistence_workbench import authoring as persistence_authoring
from router_workbench import authoring as router_authoring

SCHEMA = "spec_workbench_authoring_next.v2"
ROOT = Path(__file__).resolve().parents[1]
SEQUENCE_FILE = ROOT / "skills" / "spec-authoring" / "authoring_sequence.json"
STATE_RE = re.compile(r"\bState\s+(\d+)\b", re.IGNORECASE)


class AuthoringSequenceError(RuntimeError):
    pass


def load_sequence() -> dict[str, Any]:
    try:
        payload = json.loads(SEQUENCE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AuthoringSequenceError(f"cannot load authoring sequence: {exc}") from exc
    if payload.get("schema_version") != "spec_workbench_authoring_sequence.v2":
        raise AuthoringSequenceError("unsupported authoring sequence schema")
    if not isinstance(payload.get("phases"), list):
        raise AuthoringSequenceError("authoring sequence must contain phases")
    return payload


def _phase(sequence: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in sequence["phases"]:
        if phase.get("id") == phase_id:
            return phase
    raise AuthoringSequenceError(f"unknown authoring phase {phase_id!r}")


def _command(tool: str, project_text: str, args: list[str]) -> str:
    return shlex.join(["python", tool, project_text, *args])


def _action(
    sequence: dict[str, Any],
    phase_id: str,
    project_text: str,
    *,
    use_next: bool = False,
) -> dict[str, Any] | None:
    phase = _phase(sequence, phase_id)
    tool = phase.get("gate_tool") or phase.get("inspect_tool")
    if not tool:
        return None
    configured = phase.get("next_tool_args") if use_next else phase.get("gate_args", [])
    args = list(configured or [])
    if not phase.get("json_default") and "--json" not in args:
        args.append("--json")
    return {
        "tool": tool,
        "args": [project_text, *args],
        "command": _command(tool, project_text, args),
    }


def _result(
    *,
    sequence: dict[str, Any],
    project: Path,
    project_text: str,
    phase: str,
    blocked: bool,
    reason: str,
    summary: dict[str, Any] | None = None,
    findings: list[dict[str, Any]] | None = None,
    use_next: bool = False,
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "schema_version": SCHEMA,
        "sequence_schema_version": sequence["schema_version"],
        "project_root": project.resolve().name,
        "phase": phase,
        "blocked": blocked,
        "reason": reason,
        "action": _action(sequence, phase, project_text, use_next=use_next),
        "summary": summary or {},
        "findings": findings or [],
    }
    payload.update(extra)
    return payload


def _lint_findings(report: object) -> list[dict[str, Any]]:
    return [asdict(item) for item in getattr(report, "findings", ())]


def _has_state_source(project: Path, state: int) -> bool:
    for path in sorted(project.rglob("*.md")):
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()[:40]
        if any((match := STATE_RE.search(line)) and int(match.group(1)) == state for line in lines):
            return True
        name = path.name
        if state == 0 and (name.startswith("00_") or name == "01_product_boundary.md"):
            return True
        if state == 1 and (name.startswith("10_") or name.startswith("01_models")):
            return True
        if state == 2 and (name.startswith("20_") or name.startswith("02_rules")):
            return True
    return False


def next_step(project: Path, *, display_path: str | None = None) -> dict[str, Any]:
    """Return the first not-ready phase for one materialized project case."""
    project = project.resolve()
    if not project.is_dir():
        raise AuthoringSequenceError(f"project directory not found: {project}")
    sequence = load_sequence()
    project_text = display_path or project.as_posix()
    pending = _promoted_states_step(sequence, project, project_text)
    if pending is not None:
        return pending
    return _post_state5_step(sequence, project, project_text)


def _promoted_states_step(sequence: dict[str, Any], project: Path, project_text: str) -> dict[str, Any] | None:
    """State 0-5 chain; returns None once every promoted state gate is ready."""
    if not _has_state_source(project, 0):
        return _result(
            sequence=sequence,
            project=project,
            project_text=project_text,
            phase="state0_product_frame",
            blocked=False,
            reason="Author the State 0 product frame before deterministic model work.",
        )

    state1_source = _has_state_source(project, 1)
    try:
        state1 = design_lint.lint_project(project, state=1)
    except design_lint.DesignLintError as exc:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state1_models", blocked=True,
            reason=f"State 1 could not be inspected deterministically: {exc}",
        )
    s1 = state1.summary
    if s1.models == 0 and not state1_source:
        return _result(
            sequence=sequence,
            project=project,
            project_text=project_text,
            phase="state0_product_frame",
            blocked=False,
            reason=(
                "State 0 exists but has no deterministic acceptance gate. Review the product frame "
                "semantically; starting a State 1 source is the explicit transition out of State 0."
            ),
            summary={"manual_review_required": True},
        )
    if s1.models == 0 or s1.errors:
        if s1.models == 0 and state1_source:
            reason = "State 1 source exists but is not indexed as canonical models; normalize or migrate its model structure."
        else:
            reason = "Repair deterministic State 1 model findings."
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state1_models", blocked=bool(s1.errors), reason=reason,
            summary={"models": s1.models, "errors": s1.errors, "warnings": s1.warnings},
            findings=_lint_findings(state1),
        )

    state2_source = _has_state_source(project, 2)
    try:
        state2 = design_lint.lint_project(project, state=2)
    except design_lint.DesignLintError as exc:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state2_rules_decisions", blocked=True,
            reason=f"State 2 could not be inspected deterministically: {exc}",
        )
    s2 = state2.summary
    if s2.decisions == 0 or s2.errors:
        if s2.decisions == 0 and state2_source:
            reason = "State 2 source exists but has no indexed accepted decisions; normalize or migrate its decision structure."
        elif s2.decisions == 0:
            reason = "Author indexed State 2 accepted decisions."
        else:
            reason = "Repair deterministic State 2/security findings."
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state2_rules_decisions", blocked=bool(s2.errors), reason=reason,
            summary={"decisions": s2.decisions, "errors": s2.errors, "warnings": s2.warnings},
            findings=_lint_findings(state2),
        )

    state3 = design_stage3.lint(project)
    s3 = state3["summary"]
    if not s3["modules"] or s3["errors"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state3_module_responsibilities", blocked=bool(s3["errors"]),
            reason=("Author State 3 module responsibilities." if not s3["modules"] else "Repair deterministic State 3 module findings."),
            summary=s3, findings=state3["findings"],
        )

    trace_path = project / design_trace.DEFAULT_TRACE_FILE
    if not trace_path.is_file():
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state2_to_state3_trace", blocked=False,
            reason="Create the explicit State 2 -> State 3 ownership trace before flows.",
        )
    try:
        trace = design_trace.analyze(project)
    except (design_trace.DesignTraceError, json.JSONDecodeError, ValueError) as exc:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state2_to_state3_trace", blocked=True,
            reason=f"Repair the State 2 -> State 3 trace: {exc}",
        )
    if trace["summary"]["errors"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state2_to_state3_trace", blocked=True,
            reason="Repair ownership/disposition trace findings before State 4.",
            summary=trace["summary"], findings=trace["findings"],
        )

    state4 = design_stage4.lint(project)
    s4 = state4["summary"]
    if not s4["flows"] or s4["errors"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state4_reviewed_flows", blocked=bool(s4["errors"]),
            reason=("Author reviewed State 4 flows." if not s4["flows"] else "Repair deterministic State 4 flow findings."),
            summary=s4, findings=state4["findings"],
        )
    if (project / design_stage4.DEFAULT_PLAN_FILE).is_file():
        coverage4 = design_stage4.coverage(project)
        c4 = coverage4["summary"]
        if c4["invalid_plan_refs"] or c4["remaining"]:
            return _result(
                sequence=sequence, project=project, project_text=project_text,
                phase="state4_reviewed_flows", blocked=bool(c4["invalid_plan_refs"]),
                reason="Complete the explicit State 4 flow plan.", summary=c4, use_next=True,
            )

    state5 = design_stage5.lint(project)
    s5 = state5["summary"]
    if not s5["operations"] or s5["errors"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state5_public_module_operations", blocked=bool(s5["errors"]),
            reason=("Author State 5 public module operations." if not s5["operations"] else "Repair deterministic State 5 public-operation findings."),
            summary=s5, findings=state5["findings"],
        )
    if (project / design_stage5.DEFAULT_PLAN_FILE).is_file():
        coverage5 = design_stage5.coverage(project)
        c5 = coverage5["summary"]
        if c5["invalid_refs"] or c5["remaining"]:
            return _result(
                sequence=sequence, project=project, project_text=project_text,
                phase="state5_public_module_operations", blocked=bool(c5["invalid_refs"]),
                reason="Complete the explicit State 5 operation plan.", summary=c5, use_next=True,
            )

    return None


def _post_state5_step(sequence: dict[str, Any], project: Path, project_text: str) -> dict[str, Any]:
    """Post-State-5 chain: data closure -> contracts -> backend closures -> notes -> assembly."""
    data = design_stage6_data.lint(project)
    if data["summary"]["errors"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="pre_contract_structured_data_closure", blocked=True,
            reason="Structured data closure has deterministic errors that must be repaired before State 6 contracts.",
            summary=data["summary"],
        )

    contracts = design_stage6_contracts.handoff(project)
    if not contracts["ready"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state6_exact_contracts", blocked=False,
            reason="State 6 owns canonical Python signatures and must close before deterministic backend closure.",
            summary=contracts["summary"],
            unresolved_functions=contracts["unresolved_functions"],
            router_allowed=False, persistence_allowed=False,
        )

    persistence = persistence_authoring.coverage(project)
    if not persistence["summary"]["handoff_ready"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="deterministic_persistence_closure", blocked=bool(persistence["summary"]["errors"]),
            reason="Canonical contracts are ready; the enabled persistence_backend/v2 closure must bind repository ownership and methods to State 6 before Notes.",
            summary=persistence["summary"], findings=persistence["findings"],
            router_allowed=True, persistence_allowed=True,
        )

    router = router_authoring.coverage(project)
    if not router["summary"]["handoff_ready"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="deterministic_http_router_closure", blocked=bool(router["summary"]["errors"]),
            reason="Canonical contracts are ready; per-route Router Closure may now bind transport semantics and must validate them against State 6.",
            summary=router["summary"],
            unresolved_operations=router["unresolved_operations"],
            router_allowed=True, persistence_allowed=True,
        )

    context = design_router_context.coverage(project)
    if not context["summary"]["handoff_ready"]:
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="deterministic_http_router_context_closure", blocked=bool(context["summary"]["errors"]),
            reason="Per-route closure is ready, but global deterministic HTTP wiring/auth/error policy is not yet closed.",
            summary=context["summary"],
            unresolved_topics=context["unresolved_topics"],
            router_allowed=True, persistence_allowed=True,
        )

    notes = notes_gate.coverage(project)
    if not notes["summary"]["handoff_ready"]:
        only_missing = notes["findings"] and all(item["code"] == "missing_notes_file" for item in notes["findings"])
        return _result(
            sequence=sequence, project=project, project_text=project_text,
            phase="state7_notes",
            blocked=False if only_missing else bool(notes["summary"]["blocks"] or notes["summary"]["reviews"]),
            reason="Deterministic backend closures are closed; author State 7 notes and resolve all address/class/reference, cross-note consistency, and semantic-stub findings before handoff.",
            summary=notes["summary"], findings=notes["findings"],
            router_allowed=True, persistence_allowed=True,
        )

    return _result(
        sequence=sequence, project=project, project_text=project_text,
        phase="state8_assembly", blocked=False,
        reason="State 6 contracts, enabled deterministic backend closures, and State 7 notes gate are ready; continue to final specification assembly.",
        summary=notes["summary"],
        router_allowed=True, persistence_allowed=True,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--display-path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = next_step(args.project, display_path=args.display_path)
    except (
        AuthoringSequenceError,
        ValueError,
        json.JSONDecodeError,
        design_stage6_contracts.DesignStage6ContractsError,
        design_router_context.RouterContextError,
    ) as exc:
        print(f"design_authoring_next: error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(f"Authoring next: {payload['phase']}")
        print(payload["reason"])
        if payload.get("action"):
            print(payload["action"]["command"])
    return 1 if payload["blocked"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
