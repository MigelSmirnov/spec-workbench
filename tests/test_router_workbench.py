from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

import design_router_closure
from router_workbench import refs, service, validator
from router_workbench.model import (
    CATALOG_SCHEMA,
    COVERAGE_SCHEMA,
    LINT_SCHEMA,
    NEXT_SCHEMA,
    RouterClosureError,
)
from router_workbench.slice import semantic_operation_slice


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"
CATALOG = "70_router_closure.json"
FIRST_EXTERNAL = "public_op:durable_archive.attach_local_source"
INTERNAL_OPERATION = "public_op:access_control.authorize_operation"
UNKNOWN_OPERATION = "public_op:durable_archive.not_canonical"


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def _payload(project: Path) -> dict[str, Any]:
    return json.loads((project / CATALOG).read_text(encoding="utf-8"))


def _write(project: Path, payload: dict[str, Any]) -> None:
    (project / CATALOG).write_text(json.dumps(payload), encoding="utf-8")


def _table(operation: str, args: list[object] | None = None, *, index: int = 0) -> dict[str, object]:
    return {
        "operation": operation,
        "handler": f"synthetic_handler_{index}",
        "method": "POST",
        "path": f"/synthetic/{index}",
        "auth": "synthetic",
        "success_status": 200,
        "response_mode": "json",
        "emission": "table",
        "authorize": [],
        "delegate": {"function": "synthetic_delegate", "args": args or []},
        "projection": None,
        "returns": "delegate",
    }


def _irregular(operation: str, *, reason: str = "v1 cannot lower the accepted transport behavior", index: int = 0) -> dict[str, object]:
    return {
        "operation": operation,
        "handler": f"synthetic_irregular_{index}",
        "method": "POST",
        "path": f"/synthetic/irregular/{index}",
        "auth": "synthetic",
        "success_status": 200,
        "response_mode": "json",
        "emission": "irregular",
        "irregular_reason": reason,
    }


def _resolve_all(project: Path) -> None:
    payload = _payload(project)
    payload["items"] = [
        _table(item["operation"], [{"ref": "literal", "value": index}], index=index)
        for index, item in enumerate(payload["items"])
    ]
    _write(project, payload)


def _finding_dicts(findings: list[Any]) -> list[dict[str, Any]]:
    return [item.to_dict() if hasattr(item, "to_dict") else item for item in findings]


def _finding(
    findings: list[Any],
    code: str,
    *,
    severity: str = "error",
    operation: str | None = None,
    location: str | None = None,
    message_context: str | None = None,
) -> dict[str, Any]:
    matches = [item for item in _finding_dicts(findings) if item["code"] == code]
    assert len(matches) == 1, (code, matches)
    result = matches[0]
    assert result["severity"] == severity
    assert isinstance(result["message"], str) and result["message"].strip()
    if operation is not None:
        assert result["operation"] == operation
    if location is not None:
        assert result["location"] == location
    if message_context is not None:
        assert message_context.casefold() in result["message"].casefold()
    return result


def _codes(findings: list[Any]) -> set[str]:
    return {item["code"] for item in _finding_dicts(findings)}


# Report schemas and resolved/unresolved readiness


def test_cabinet_coverage_schema_is_closed_and_resolved() -> None:
    report = service.coverage(CABINET)
    assert set(report) == {"schema_version", "project_root", "summary", "unresolved_operations", "findings"}
    assert report["schema_version"] == COVERAGE_SCHEMA
    assert report["project_root"] == "cabinet-backend"
    assert set(report["summary"]) == {
        "external_operations", "catalog_items", "resolved", "unresolved", "errors", "handoff_ready",
    }
    assert report["summary"] == {
        "external_operations": 13,
        "catalog_items": 13,
        "resolved": 13,
        "unresolved": 0,
        "errors": 0,
        "handoff_ready": True,
    }
    assert report["unresolved_operations"] == []
    assert report["findings"] == []


def test_fully_resolved_synthetic_cabinet_is_handoff_ready(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _resolve_all(project)
    report = service.coverage(project)
    assert report["summary"] == {
        "external_operations": 13,
        "catalog_items": 13,
        "resolved": 13,
        "unresolved": 0,
        "errors": 0,
        "handoff_ready": True,
    }
    assert report["unresolved_operations"] == []
    assert report["findings"] == []
    next_report = service.next_operation(project)
    assert set(next_report) == {"schema_version", "project_root", "complete", "next", "summary"}
    assert next_report["schema_version"] == NEXT_SCHEMA
    assert next_report["complete"] is True
    assert next_report["next"] is None


def test_fully_resolved_catalog_counts_irregular_as_resolved(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _resolve_all(project)
    payload = _payload(project)
    payload["irregular_ownership"] = {"module": "api_irregular"}
    payload["items"][0] = _irregular(payload["items"][0]["operation"])
    _write(project, payload)
    report = service.coverage(project)
    assert report["summary"]["resolved"] == 13
    assert report["summary"]["unresolved"] == 0
    assert report["summary"]["errors"] == 0
    assert report["summary"]["handoff_ready"] is True


def test_resolved_and_unresolved_counts_are_exact(tmp_path: Path) -> None:
    project = _project(tmp_path)
    payload = _payload(project)
    payload["items"][0] = _table(payload["items"][0]["operation"])
    _write(project, payload)
    summary = service.coverage(project)["summary"]
    assert summary["resolved"] == 1
    assert summary["unresolved"] == 12
    assert summary["handoff_ready"] is False


def test_resolution_is_not_sufficient_when_validation_fails(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _resolve_all(project)
    payload = _payload(project)
    payload["items"][0]["delegate"]["args"] = ["payload.invoice_id"]
    _write(project, payload)
    report = service.coverage(project)
    assert report["summary"]["resolved"] == 13
    assert report["summary"]["unresolved"] == 0
    assert report["summary"]["errors"] == 1
    assert report["summary"]["handoff_ready"] is False
    _finding(report["findings"], "python_string_arg", operation=FIRST_EXTERNAL, location="items[0].delegate.args[0]")


def test_lint_and_next_report_schemas_are_closed() -> None:
    lint = service.lint(CABINET)
    assert set(lint) == {"schema_version", "project_root", "summary", "findings"}
    assert lint["schema_version"] == LINT_SCHEMA
    assert set(lint["summary"]) == {
        "external_operations", "catalog_items", "resolved", "unresolved", "errors", "handoff_ready", "warnings",
    }
    assert lint["summary"]["warnings"] == 0
    assert [item["operation"] for item in lint["findings"]] == sorted(item["operation"] for item in lint["findings"])
    assert lint["findings"] == []

    next_report = service.next_operation(CABINET)
    assert set(next_report) == {"schema_version", "project_root", "complete", "next", "summary"}
    assert next_report["schema_version"] == NEXT_SCHEMA
    assert next_report["complete"] is True
    assert next_report["next"] is None


# Typed refs: the closed http_router_backend/v1 language


@pytest.mark.parametrize("typed_ref", [
    {"ref": "slot", "name": "store"},
    {"ref": "credential", "name": "bearer"},
    {"ref": "parameter", "path": ["payload", "invoice_id"]},
    {"ref": "enum", "type": "Capability", "member": "INVOICE_READ"},
    {"ref": "literal", "value": None},
    {"ref": "literal", "value": True},
    {"ref": "literal", "value": 42},
    {"ref": "literal", "value": "accepted"},
])
def test_each_normative_v1_typed_ref_is_accepted(typed_ref: dict[str, object]) -> None:
    assert refs.validate_ref(typed_ref, operation=FIRST_EXTERNAL, location="args[0]") == []


@pytest.mark.parametrize(("typed_ref", "missing_context"), [
    ({"ref": "slot"}, "name"),
    ({"ref": "credential"}, "name"),
    ({"ref": "parameter"}, "path"),
    ({"ref": "enum", "member": "X"}, "type"),
    ({"ref": "enum", "type": "Capability"}, "member"),
    ({"ref": "literal"}, "value"),
])
def test_typed_ref_missing_required_field_is_rejected(typed_ref: dict[str, object], missing_context: str) -> None:
    findings = refs.validate_ref(typed_ref, operation=FIRST_EXTERNAL, location="delegate.args[0]")
    finding = _finding(findings, "missing_ref_field", operation=FIRST_EXTERNAL, location="delegate.args[0]")
    assert missing_context in finding["message"]


def test_typed_ref_extra_field_is_rejected() -> None:
    findings = refs.validate_ref(
        {"ref": "slot", "name": "store", "expression": "store.value"},
        operation=FIRST_EXTERNAL,
        location="delegate.args[0]",
    )
    finding = _finding(findings, "unknown_ref_field", operation=FIRST_EXTERNAL, location="delegate.args[0]")
    assert "expression" in finding["message"]


@pytest.mark.parametrize(("typed_ref", "code"), [
    ({"ref": "slot", "name": 1}, "invalid_ref_name"),
    ({"ref": "credential", "name": None}, "invalid_ref_name"),
    ({"ref": "parameter", "path": "payload.id"}, "invalid_parameter_path"),
    ({"ref": "parameter", "path": []}, "invalid_parameter_path"),
    ({"ref": "parameter", "path": ["payload", 1]}, "invalid_parameter_path"),
    ({"ref": "enum", "type": 1, "member": "READ"}, "invalid_enum_ref"),
    ({"ref": "enum", "type": "Capability", "member": []}, "invalid_enum_ref"),
    ({"ref": "literal", "value": []}, "invalid_literal_ref"),
    ({"ref": "literal", "value": {}}, "invalid_literal_ref"),
])
def test_typed_ref_wrong_field_shape_is_rejected(typed_ref: dict[str, object], code: str) -> None:
    findings = refs.validate_ref(typed_ref, operation=FIRST_EXTERNAL, location="delegate.args[0]")
    _finding(findings, code, operation=FIRST_EXTERNAL, location="delegate.args[0]")


def test_unknown_ref_kind_is_rejected_with_context() -> None:
    findings = refs.validate_ref(
        {"ref": "expression", "value": "payload.invoice_id"},
        operation=FIRST_EXTERNAL,
        location="delegate.args[0]",
    )
    _finding(
        findings,
        "unknown_ref_kind",
        operation=FIRST_EXTERNAL,
        location="delegate.args[0]",
        message_context="expression",
    )


@pytest.mark.parametrize(("value", "code"), [
    ("payload.invoice_id", "python_string_arg"),
    (None, "invalid_ref"),
    (42, "invalid_ref"),
])
def test_non_object_argument_is_rejected(value: object, code: str) -> None:
    findings = refs.validate_ref(value, operation=FIRST_EXTERNAL, location="delegate.args[0]")
    _finding(findings, code, operation=FIRST_EXTERNAL, location="delegate.args[0]")


def test_args_must_be_a_list_and_nested_args_are_traversed() -> None:
    invalid_list = refs.validate_argument_refs(
        {"delegate": {"args": "payload.id"}}, operation=FIRST_EXTERNAL, location="items[0]"
    )
    _finding(invalid_list, "invalid_args", operation=FIRST_EXTERNAL, location="items[0].delegate.args")
    nested = refs.validate_argument_refs(
        {"authorize": [{"call": {"args": ["actor.id"]}}]}, operation=FIRST_EXTERNAL, location="items[0]"
    )
    _finding(nested, "python_string_arg", operation=FIRST_EXTERNAL, location="items[0].authorize[0].call.args[0]")


# Validator: emission shapes and fail-closed catalog semantics


def test_each_emission_has_a_distinct_valid_shape() -> None:
    unresolved = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [{"operation": FIRST_EXTERNAL, "emission": "unresolved"}]}
    table = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [_table(FIRST_EXTERNAL)]}
    irregular = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": {"module": "api_irregular"}, "items": [_irregular(FIRST_EXTERNAL)]}
    assert validator.validate(unresolved) == []
    assert validator.validate(table) == []
    assert validator.validate(irregular) == []


@pytest.mark.parametrize(("item", "unexpected_field"), [
    ({"operation": FIRST_EXTERNAL, "emission": "unresolved", "handler": "hidden"}, "handler"),
    ({**_table(FIRST_EXTERNAL), "irregular_reason": "not a table field"}, "irregular_reason"),
    ({**_irregular(FIRST_EXTERNAL), "delegate": {"function": "x", "args": []}}, "delegate"),
])
def test_emission_shapes_reject_fields_from_other_states(item: dict[str, object], unexpected_field: str) -> None:
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": {"module": "api_irregular"}, "items": [item]}
    finding = _finding(validator.validate(payload), "unknown_item_field", operation=FIRST_EXTERNAL, location="items[0]")
    assert unexpected_field in finding["message"]


@pytest.mark.parametrize("field", [
    "body", "code", "implementation", "pseudo_code", "pseudocode", "python", "python_body", "signature", "source",
])
def test_executable_signature_and_pseudocode_fields_are_forbidden_at_item_level(field: str) -> None:
    item = {"operation": FIRST_EXTERNAL, "emission": "unresolved", field: "return do_work()"}
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [item]}
    findings = validator.validate(payload)
    assert {"unknown_item_field", "hidden_python_body"}.issubset(_codes(findings))
    _finding(findings, "hidden_python_body", operation=FIRST_EXTERNAL, location=f"items[0].{field}", message_context=field)


def test_signature_is_forbidden_when_nested_in_table_call() -> None:
    item = _table(FIRST_EXTERNAL)
    item["delegate"]["signature"] = "(payload: Payload) -> Result"
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [item]}
    _finding(
        validator.validate(payload),
        "hidden_python_body",
        operation=FIRST_EXTERNAL,
        location="items[0].delegate.signature",
        message_context="signature",
    )


def test_hidden_code_scan_traverses_lists_with_operation_and_location() -> None:
    item = _table(FIRST_EXTERNAL)
    item["authorize"] = [{"steps": [{"signature": "(actor) -> bool"}]}]
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [item]}
    _finding(
        validator.validate(payload),
        "hidden_python_body",
        operation=FIRST_EXTERNAL,
        location="items[0].authorize[0].steps[0].signature",
        message_context="signature",
    )


def test_irregular_requires_reason_and_companion_ownership() -> None:
    item = _irregular(FIRST_EXTERNAL, reason="")
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [item]}
    findings = validator.validate(payload)
    _finding(findings, "missing_irregular_reason", operation=FIRST_EXTERNAL, location="items[0]")
    _finding(findings, "missing_irregular_ownership", message_context="companion")


@pytest.mark.parametrize("ownership", [
    {},
    {"module": ""},
    {"module": 1},
    {"module": "api_irregular", "extra": True},
    "api_irregular",
])
def test_irregular_ownership_shape_is_closed(ownership: object) -> None:
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": ownership, "items": [_irregular(FIRST_EXTERNAL)]}
    _finding(validator.validate(payload), "invalid_irregular_ownership", message_context="module")


def test_unknown_root_and_item_fields_fail_closed() -> None:
    payload = {
        "schema_version": CATALOG_SCHEMA,
        "irregular_ownership": None,
        "items": [{"operation": FIRST_EXTERNAL, "emission": "unresolved", "mystery": True}],
        "parallel_dsl": {},
    }
    findings = validator.validate(payload)
    root = _finding(findings, "unknown_catalog_field", message_context="parallel_dsl")
    assert set(root) == {"severity", "code", "message"}
    _finding(findings, "unknown_item_field", operation=FIRST_EXTERNAL, location="items[0]", message_context="mystery")


@pytest.mark.parametrize(("payload", "code", "location"), [
    ({"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": None}, "invalid_items", None),
    ({"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [None]}, "invalid_item", "items[0]"),
    ({"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [{"operation": "bad", "emission": "unresolved"}]}, "invalid_operation_ref", "items[0]"),
    ({"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [{"operation": FIRST_EXTERNAL, "emission": "future"}]}, "invalid_emission", "items[0]"),
])
def test_malformed_catalog_items_are_errors_not_warnings(payload: dict[str, Any], code: str, location: str | None) -> None:
    findings = validator.validate(payload)
    finding = _finding(findings, code, location=location)
    assert finding["severity"] == "error"
    assert all(item["severity"] == "error" for item in _finding_dicts(findings))
    if code == "invalid_operation_ref":
        assert finding["operation"] == "bad"


def test_validator_reports_every_malformed_item_in_deterministic_order() -> None:
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [None, 42]}
    findings = _finding_dicts(validator.validate(payload))
    assert [item["code"] for item in findings] == ["invalid_item", "invalid_item"]
    assert [item["location"] for item in findings] == ["items[0]", "items[1]"]
    assert all(isinstance(item["message"], str) and item["message"] for item in findings)


def test_invalid_emission_has_only_its_canonical_diagnostic() -> None:
    payload = {
        "schema_version": CATALOG_SCHEMA,
        "irregular_ownership": None,
        "items": [{"operation": FIRST_EXTERNAL, "emission": "future"}],
    }
    findings = _finding_dicts(validator.validate(payload))
    assert [item["code"] for item in findings] == ["invalid_emission"]
    _finding(findings, "invalid_emission", operation=FIRST_EXTERNAL, location="items[0]", message_context="emission")


def test_table_missing_required_fields_is_an_error_with_context() -> None:
    payload = {"schema_version": CATALOG_SCHEMA, "irregular_ownership": None, "items": [{"operation": FIRST_EXTERNAL, "emission": "table"}]}
    finding = _finding(validator.validate(payload), "missing_item_field", operation=FIRST_EXTERNAL, location="items[0]")
    assert "delegate" in finding["message"]
    assert "handler" in finding["message"]


# Coverage ownership, determinism, and readiness


@pytest.mark.parametrize(("mutation", "code", "operation"), [
    ("missing", "missing_external_operation", "public_op:retention_release.request_manual_vps_release"),
    ("duplicate", "duplicate_operation", FIRST_EXTERNAL),
    ("internal", "internal_only_exposed", INTERNAL_OPERATION),
    ("unknown", "unknown_public_operation", UNKNOWN_OPERATION),
])
def test_coverage_boundary_violations_have_complete_findings(
    tmp_path: Path, mutation: str, code: str, operation: str
) -> None:
    project = _project(tmp_path)
    payload = _payload(project)
    if mutation == "missing":
        payload["items"].pop()
    elif mutation == "duplicate":
        payload["items"].append(dict(payload["items"][0]))
    else:
        payload["items"][0] = _table(operation)
    _write(project, payload)
    report = service.coverage(project)
    finding = _finding(
        report["findings"],
        code,
        operation=operation,
        location=f"{CATALOG}:items",
        message_context="operation",
    )
    assert set(finding) == {"severity", "code", "message", "operation", "location"}
    assert report["summary"]["errors"] >= 1
    assert report["summary"]["handoff_ready"] is False
    if mutation == "duplicate":
        assert report["summary"]["catalog_items"] == 14
        assert report["summary"]["resolved"] == 0
        assert report["summary"]["unresolved"] == 13
    if mutation in {"internal", "unknown"}:
        assert report["summary"]["resolved"] == 0
        assert report["summary"]["unresolved"] == 13


def test_catalog_order_does_not_change_coverage_or_next(tmp_path: Path) -> None:
    project = _project(tmp_path)
    original_coverage = service.coverage(project)
    original_next = service.next_operation(project)["next"]["operation"]
    payload = _payload(project)
    payload["items"].reverse()
    _write(project, payload)
    assert service.coverage(project) == original_coverage
    assert service.next_operation(project)["next"]["operation"] == original_next == FIRST_EXTERNAL


def test_report_serialization_is_byte_stable_for_identical_input() -> None:
    first = json.dumps(service.lint(CABINET), ensure_ascii=False, indent=2, sort_keys=True)
    second = json.dumps(service.lint(CABINET), ensure_ascii=False, indent=2, sort_keys=True)
    assert first == second


def test_unknown_semantic_operation_slice_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown module"):
        semantic_operation_slice(CABINET, "public_op:does_not_exist.operation")


@pytest.mark.parametrize("operation", ["durable_archive.operation", "public_op:durable_archive"])
def test_malformed_semantic_operation_key_is_rejected(operation: str) -> None:
    with pytest.raises(RouterClosureError, match="invalid public operation key"):
        semantic_operation_slice(CABINET, operation)


def test_unknown_operation_in_known_module_is_rejected() -> None:
    with pytest.raises(RouterClosureError, match="absent from its semantic module slice"):
        semantic_operation_slice(CABINET, UNKNOWN_OPERATION)


# CLI modes and exit-code contract


def test_cli_lint_json_success_and_schema(capsys: pytest.CaptureFixture[str]) -> None:
    assert design_router_closure.main([str(CABINET), "--lint", "--json"]) == 0
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert output.err == ""
    assert payload["schema_version"] == LINT_SCHEMA
    assert payload["summary"]["warnings"] == 0


def test_cli_lint_validation_failure_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = _project(tmp_path)
    payload = _payload(project)
    payload["items"][0]["operation"] = UNKNOWN_OPERATION
    _write(project, payload)
    assert design_router_closure.main([str(project), "--lint", "--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["schema_version"] == LINT_SCHEMA
    assert report["summary"]["errors"] > 0


def test_cli_coverage_readiness_failure_returns_one(capsys: pytest.CaptureFixture[str]) -> None:
    assert design_router_closure.main([str(CABINET), "--coverage", "--json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == COVERAGE_SCHEMA
    assert payload["summary"]["handoff_ready"] is False


def test_cli_coverage_success_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = _project(tmp_path)
    _resolve_all(project)
    assert design_router_closure.main([str(project), "--coverage", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == COVERAGE_SCHEMA
    assert payload["summary"]["handoff_ready"] is True


def test_cli_next_json_success_and_schema(capsys: pytest.CaptureFixture[str]) -> None:
    assert design_router_closure.main([str(CABINET), "--next", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == NEXT_SCHEMA
    assert payload["next"]["operation"] == FIRST_EXTERNAL


def test_cli_next_complete_project_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = _project(tmp_path)
    _resolve_all(project)
    assert design_router_closure.main([str(project), "--next", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["complete"] is True
    assert payload["next"] is None


def test_next_is_not_complete_when_all_items_are_resolved_but_invalid(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _resolve_all(project)
    payload = _payload(project)
    payload["items"][0]["delegate"]["args"] = ["payload.invoice_id"]
    _write(project, payload)
    report = service.next_operation(project)
    assert report["next"] is None
    assert report["summary"]["unresolved"] == 0
    assert report["summary"]["handoff_ready"] is False
    assert report["complete"] is False


def test_cli_json_output_is_byte_stable(capsys: pytest.CaptureFixture[str]) -> None:
    assert design_router_closure.main([str(CABINET), "--coverage", "--json"]) == 1
    first = capsys.readouterr().out
    assert design_router_closure.main([str(CABINET), "--coverage", "--json"]) == 1
    second = capsys.readouterr().out
    assert first == second
    assert json.loads(first)["schema_version"] == COVERAGE_SCHEMA


def test_cli_missing_project_returns_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "missing"
    assert design_router_closure.main([str(missing), "--lint"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "project directory not found" in output.err


def test_cli_malformed_catalog_returns_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = _project(tmp_path)
    (project / CATALOG).write_text("{not-json", encoding="utf-8")
    assert design_router_closure.main([str(project), "--lint", "--json"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert "invalid" in output.err.casefold()
    assert CATALOG in output.err


def test_cli_missing_catalog_returns_two(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    project = _project(tmp_path)
    (project / CATALOG).unlink()
    assert design_router_closure.main([str(project), "--coverage"]) == 2
    output = capsys.readouterr()
    assert output.out == ""
    assert f"missing {CATALOG}" in output.err


def test_cli_usage_error_is_argparse_exit_two() -> None:
    with pytest.raises(SystemExit) as exc_info:
        design_router_closure.main([str(CABINET)])
    assert exc_info.value.code == 2
