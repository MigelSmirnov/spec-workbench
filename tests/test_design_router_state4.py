from __future__ import annotations

from pathlib import Path

import design_router


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    project.mkdir()
    return project


def test_diagnose_state4_uses_stage4_lint(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "diagnose-state4")
    assert [step.id for step in plan.steps] == ["state4_lint", "review_findings"]
    assert plan.steps[0].tool == "design_stage4"
    assert "--lint --json" in plan.steps[0].command


def test_inspect_flow_accepts_stable_flow_key(tmp_path: Path) -> None:
    plan = design_router.route(
        _project(tmp_path), "inspect-flow", item="flow:synchronize_invoice_to_local_archive"
    )
    assert [step.id for step in plan.steps] == ["state4_get"]
    assert plan.steps[0].arguments["flow"] == "flow:synchronize_invoice_to_local_archive"
    assert "--get flow:synchronize_invoice_to_local_archive --json" in plan.steps[0].command


def test_state4_handoff_is_machine_readable(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "state4-handoff")
    assert [step.id for step in plan.steps] == ["state4_handoff"]
    assert plan.steps[0].tool == "design_stage4"
    assert plan.steps[0].arguments["consumer"] == "next_design_state_or_mcp"
    assert "tools/design_stage4.py" in plan.steps[0].command
    assert "--handoff" in plan.steps[0].command


def test_verify_state4_checks_prerequisites_before_tests(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "verify-state4")
    assert [step.id for step in plan.steps] == [
        "rebuild_index",
        "state3_lint",
        "trace_2_3_check",
        "state4_lint",
        "review_findings",
        "state4_handoff",
        "run_tests",
    ]
    assert plan.steps[3].tool == "design_stage4"
    assert plan.steps[-1].tool == "pytest"
