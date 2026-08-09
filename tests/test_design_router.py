from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest

import design_router


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    project.mkdir()
    return project


def _content(tmp_path: Path) -> Path:
    path = tmp_path / "content.md"
    path.write_text("### Required tests\n\n1. Verify it.\n", encoding="utf-8")
    return path


def test_route_table_is_complete_and_names_only_supported_tools() -> None:
    routes = design_router.load_routes()

    assert routes["schema_version"] == "spec_workbench_design_routes.v1"
    assert set(routes["editor_operations"]) == design_router.SUPPORTED_EDITOR_OPERATIONS
    assert {
        step.get("tool")
        for step in routes["steps"].values()
        if step.get("tool") is not None
    } <= design_router.SUPPORTED_TOOLS


def test_inventory_starts_with_indexed_items(tmp_path: Path) -> None:
    project = _project(tmp_path)

    plan = design_router.route(project, "inventory", state=2, kind="decision")

    assert plan.read_only is True
    assert plan.executes_commands is False
    assert [step.id for step in plan.steps] == ["list_items"]
    assert plan.steps[0].tool == "design_index"
    assert plan.steps[0].arguments == {
        "project": project.as_posix(),
        "state": 2,
        "kind": "decision",
    }
    assert "--list --state 2 --kind decision" in plan.steps[0].command


def test_inspect_item_routes_through_structure_and_references(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "inspect-item", item="A51")

    assert [step.id for step in plan.steps] == [
        "get_item",
        "item_references",
        "selective_context",
    ]
    assert plan.steps[0].arguments["item"] == "A51"
    assert plan.steps[1].arguments["item"] == "A51"
    assert plan.steps[2].kind == "conditional"
    assert "$previous_result" in plan.steps[2].arguments["location"]


def test_trace_term_preserves_required_broad_to_narrow_loop(tmp_path: Path) -> None:
    plan = design_router.route(
        _project(tmp_path),
        "trace-term",
        term="Holded",
        state=2,
        kind="decision",
    )

    assert [step.id for step in plan.steps] == [
        "broad_mentions",
        "selective_context",
        "narrow_mentions",
        "candidate_references",
        "operator_judgment",
    ]
    assert plan.steps[0].arguments["term"] == "Holded"
    assert plan.steps[2].arguments["state"] == 2
    assert plan.steps[-1].kind == "checkpoint"
    assert "must not be inferred" in plan.steps[-1].why


def test_diagnose_uses_contextual_lint_then_operator_review(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "diagnose-state2")

    assert [step.id for step in plan.steps] == [
        "lint_state2",
        "review_findings",
    ]
    assert plan.steps[0].arguments["context"] is True
    assert "--compact" not in plan.steps[0].command
    assert plan.steps[1].kind == "checkpoint"


@pytest.mark.parametrize(
    "operation,kwargs,expected_tail",
    [
        (
            "replace-section",
            {"section": "Consequence"},
            ["replace-section", "A51", "Consequence"],
        ),
        (
            "append-section",
            {"section": "Required tests"},
            ["append-section", "A51", "Required tests"],
        ),
        (
            "insert-section",
            {"after_section": "Formal invariants"},
            ["insert-section", "A51", "Formal invariants"],
        ),
        (
            "replace-item",
            {},
            ["replace-item", "A51"],
        ),
    ],
)
def test_edit_route_supports_exactly_the_editor_v1_operations(
    tmp_path: Path,
    operation: str,
    kwargs: dict[str, str],
    expected_tail: list[str],
) -> None:
    project = _project(tmp_path)
    content = _content(tmp_path)

    plan = design_router.route(
        project,
        "edit-fragment",
        operation=operation,
        item="A51",
        content_file=content,
        **kwargs,
    )

    dry_run = next(step for step in plan.steps if step.id == "editor_dry_run")
    command_words = shlex.split(dry_run.command)
    assert command_words[3:3 + len(expected_tail)] == expected_tail
    assert dry_run.arguments["apply"] is False


def test_edit_route_enforces_dry_run_review_apply_and_verification_order(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    content = _content(tmp_path)

    plan = design_router.route(
        project,
        "edit-fragment",
        operation="insert-section",
        item="A42",
        after_section="Normative rules",
        content_file=content,
    )

    assert [step.id for step in plan.steps] == [
        "get_item",
        "editor_dry_run",
        "review_diff",
        "editor_apply",
        "rebuild_index",
        "lint_state2",
        "review_findings",
        "run_tests",
    ]
    dry_run = plan.steps[1]
    apply = plan.steps[3]
    assert "--apply" not in dry_run.command
    assert apply.command.endswith("--apply")
    assert apply.requires == (
        "editor dry-run succeeded",
        "operator reviewed the complete unified diff",
    )
    assert plan.steps[2].kind == "checkpoint"
    assert plan.steps[4].tool == "design_index"
    assert plan.steps[5].tool == "design_lint"
    assert plan.steps[7].tool == "pytest"


@pytest.mark.parametrize(
    "kwargs,message",
    [
        ({"operation": "insert-section", "item": "A1"}, "content_file is required"),
        ({"operation": "insert-section", "item": "A1", "content_file": Path("missing")}, "content file not found"),
        ({"operation": "insert-section", "item": "A1", "content_file": None}, "content_file is required"),
    ],
)
def test_edit_route_fails_closed_on_incomplete_inputs(
    tmp_path: Path,
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(design_router.DesignRouterError, match=message):
        design_router.route(_project(tmp_path), "edit-fragment", **kwargs)


def test_insert_requires_after_section_and_replace_requires_section(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    content = _content(tmp_path)

    with pytest.raises(design_router.DesignRouterError, match="after_section is required"):
        design_router.route(
            project,
            "edit-fragment",
            operation="insert-section",
            item="A1",
            content_file=content,
        )
    with pytest.raises(design_router.DesignRouterError, match="section is required"):
        design_router.route(
            project,
            "edit-fragment",
            operation="replace-section",
            item="A1",
            content_file=content,
        )


def test_unsupported_semantic_mutations_are_not_routable(tmp_path: Path) -> None:
    with pytest.raises(design_router.DesignRouterError, match="unsupported editor operation"):
        design_router.route(
            _project(tmp_path),
            "edit-fragment",
            operation="rename-item",
            item="A1",
            content_file=_content(tmp_path),
        )


def test_verify_orders_index_lint_review_and_tests(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "verify")

    assert [step.id for step in plan.steps] == [
        "rebuild_index",
        "lint_state2",
        "review_findings",
        "run_tests",
    ]
    assert plan.steps[-1].next_on_success is None
    assert all(
        step.next_on_success == plan.steps[index + 1].id
        for index, step in enumerate(plan.steps[:-1])
    )


def test_json_is_stable_and_contains_no_factory_route(tmp_path: Path) -> None:
    plan = design_router.route(_project(tmp_path), "diagnose-state2")

    first = design_router.render_json(plan)
    second = design_router.render_json(plan)
    payload = json.loads(first)

    assert first == second
    assert first.endswith("\n")
    assert payload["schema_version"] == "spec_workbench_design_route_plan.v1"
    assert "factory" not in first.casefold()
    assert payload["executes_commands"] is False


def test_cli_emits_machine_readable_plan(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = _project(tmp_path)

    assert design_router.main([str(project), "inventory", "--json"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["intent"] == "inventory"
    assert payload["steps"][0]["tool"] == "design_index"
    assert captured.err == ""


def test_missing_project_is_analysis_failure(tmp_path: Path) -> None:
    with pytest.raises(design_router.DesignRouterError, match="project directory not found"):
        design_router.route(tmp_path / "missing", "inventory")


def test_unknown_intent_and_invalid_filters_fail_closed(tmp_path: Path) -> None:
    project = _project(tmp_path)

    with pytest.raises(design_router.DesignRouterError, match="unknown intent"):
        design_router.route(project, "invent-workflow")
    with pytest.raises(design_router.DesignRouterError, match="state must be non-negative"):
        design_router.route(project, "inventory", state=-1)
    with pytest.raises(design_router.DesignRouterError, match="unsupported item kind"):
        design_router.route(project, "inventory", kind="artifact")
    with pytest.raises(design_router.DesignRouterError, match="term is required"):
        design_router.route(project, "trace-term", term="   ")


def test_global_guards_keep_semantics_and_unsupported_edits_with_operator(
    tmp_path: Path,
) -> None:
    plan = design_router.route(_project(tmp_path), "inventory")
    rendered = "\n".join(plan.global_stop_conditions)

    assert "semantic content has not been supplied or accepted by the operator" in rendered
    assert "rename, move, delete" in rendered
    assert "duplicate item keys" in rendered


def test_route_table_rejects_an_unknown_step(tmp_path: Path) -> None:
    routes = design_router.load_routes()
    routes["intents"]["inventory"]["steps"] = ["invent_semantics"]
    path = tmp_path / "routes.json"
    path.write_text(json.dumps(routes), encoding="utf-8")

    with pytest.raises(design_router.DesignRouterError, match="unknown steps"):
        design_router.load_routes(path)
