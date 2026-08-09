from __future__ import annotations

from pathlib import Path

import design_router


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    project.mkdir()
    return project


def test_diagnose_state3_uses_stage3_lint(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "diagnose-state3")

    assert [step.id for step in plan.steps] == ["state3_lint", "review_findings"]
    assert plan.steps[0].tool == "design_stage3"
    assert "--lint --json" in plan.steps[0].command


def test_inspect_module_accepts_stable_module_key(tmp_path: Path) -> None:
    plan = design_router.route(
        _project(tmp_path), "inspect-module", item="module:durable_archive"
    )

    assert [step.id for step in plan.steps] == ["state3_get"]
    assert plan.steps[0].arguments["module"] == "module:durable_archive"
    assert "--get module:durable_archive --json" in plan.steps[0].command


def test_state3_trace_is_explicit_before_operator_judgment(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "trace-state2-to-state3")

    assert [step.id for step in plan.steps] == ["state3_trace", "operator_judgment"]
    assert plan.steps[0].arguments["from_state"] == 2
    assert plan.steps[0].arguments["to_state"] == 3
    assert plan.steps[0].tool == "design_stage3"


def test_handoff_is_machine_readable_and_next_state_friendly(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "state3-handoff")

    assert [step.id for step in plan.steps] == ["state3_handoff"]
    assert plan.steps[0].arguments["consumer"] == "next_design_state"
    assert "--handoff --json" in plan.steps[0].command


def test_verify_state3_orders_trace_handoff_before_tests(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "verify-state3")

    assert [step.id for step in plan.steps] == [
        "rebuild_index",
        "state3_lint",
        "state3_trace",
        "review_findings",
        "state3_handoff",
        "run_tests",
    ]
    assert plan.steps[1].tool == "design_stage3"
    assert plan.steps[2].tool == "design_stage3"
    assert plan.steps[4].tool == "design_stage3"
    assert plan.steps[-1].tool == "pytest"
