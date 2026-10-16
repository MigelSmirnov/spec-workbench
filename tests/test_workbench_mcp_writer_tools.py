"""The notes-writer tools of the Workbench MCP service (Data Closure §4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import spec_projection_workbench
from questions_workbench import documents as question_documents
from workbench_mcp import service

SPEC = {
    "standard_version": 3,
    "models": {"Status": {"kind": "enum", "values": ["open", "closed"]}, "Row": {"fields": {"row_id": "str"}}},
    "rules": {"data_provider_backend": {"kind": "data_provider_backend",
                                        "constants": {"PAGE_MAX": {"value_type": "positive_integer", "value": 200}}}},
    "config": {},
    "contracts": {"load_rows": "(limit: int) -> list[Row]", "save_rows": "(rows: list[Row]) -> None"},
    "module_functions": {"alpha": ["save_rows"], "store": ["load_rows"], "models": ["Row", "Status"]},
}
SPAN = "MUST sort the rows by the declared keys before hashing them so that equal content"


@pytest.fixture
def case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "case"
    root.mkdir()
    (root / "80_notes.md").write_text(
        "load_rows: [BEHAVIOR] MUST return rows in store order.\n"
        f"save_rows: [BEHAVIOR] {SPAN}: by (row_id, row_name, row_kind).\n", encoding="utf-8"
    )
    (root / "30_modules.md").write_text("## `module:alpha`\n## `module:store`\n", encoding="utf-8")
    (root / "60_contracts.json").write_text(json.dumps({
        "schema_version": "spec_workbench_state6_contracts.v1", "contracts": SPEC["contracts"],
    }), encoding="utf-8")
    (root / "global_spec.json").write_text(json.dumps({"standard_version": 3}), encoding="utf-8")
    monkeypatch.setattr(spec_projection_workbench, "projected_spec", lambda project: json.loads(json.dumps(SPEC)))
    return root


def _real_factory() -> Path:
    root = question_documents.factory_root()
    version = root / "tools/spec_version.py" if root else None
    if version is None or "NOTE_ADDRESSES_CLOSED_MIN_VERSION" not in version.read_text(encoding="utf-8"):
        pytest.skip("no Factory checkout that closes note addresses (code-factory #87)")
    return root


def test_m2_value_homes(case):
    answer = service.value_homes(case, "200")
    assert answer["homes_reaching_code"] == ["the imported PAGE_MAX constant"]
    assert service.value_homes(case, "30")["homes"] == []


def test_m4_absence_carries_namespace_digests(case):
    answer = service.absence(case, ["timeout"])
    assert answer["terms"] == {"timeout": []}
    assert set(answer["namespaces"]) == {"models", "rules", "config", "contracts"}


def test_m6_module_notes(case):
    answer = service.module_notes(case, "store")
    assert answer["callables"] == ["load_rows"]
    assert [n["scope"] for n in answer["notes"]] == ["load_rows"]
    with pytest.raises(ValueError):
        service.module_notes(case, "nowhere")


def test_m1_resolves_through_the_factory(case):
    factory = _real_factory()
    assert service.resolve_address(case, "= models.Status", factory)["status"] == "legal"
    closed = service.resolve_address(case, "= rules.data_provider_backend.constants.PAGE_MAX", factory)
    assert (closed["status"], closed["code"]) == ("illegal", "address_form_closed")


def test_draft_check_names_the_module_and_the_findings(case):
    factory = _real_factory()
    clean = service.check_note_draft(case, "load_rows: [BEHAVIOR] MUST return at most the imported PAGE_MAX constant rows.", factory)
    assert (clean["module"], clean["clean"], clean["findings"]) == ("store", True, [])
    dirty = service.check_note_draft(case, "load_rows: [BEHAVIOR] MUST return at most 200 rows of = rules.x.", factory)
    assert not dirty["clean"]
    assert [(f["rule"], f["code"]) for f in dirty["findings"]] == [
        ("gate", "address_form_closed"), ("L2", "literal_with_home")]


@pytest.mark.parametrize("note, code", [
    ("load_rows: [RULE_REFERENCE] MUST return the source.", "note_class_closed"),
    ("load_rows: [NOT_A_CLASS] MUST return rows.", "unknown_note_class"),
    ("nowhere: [BEHAVIOR] MUST return rows.", "unknown_note_scope"),
])
def test_draft_check_applies_the_gates_own_checks(case, note, code):
    factory = _real_factory()
    answer = service.check_note_draft(case, note, factory)
    assert not answer["clean"] and code in {f["code"] for f in answer["findings"]}


def test_draft_check_sees_a_diverged_copy_whatever_the_module_order(case):
    factory = _real_factory()
    answer = service.check_note_draft(case, f"load_rows: [BEHAVIOR] {SPAN}: by (row_id, row_kind, row_name).", factory)
    assert {"shared_prose", "diverged_copies"} <= {f["code"] for f in answer["findings"]}


@pytest.mark.parametrize("text", ["MUST do something", "load_rows: [BEHAVIOR] MUST return rows.\u2028save_rows: [BEHAVIOR] MAY skip."])
def test_draft_check_refuses_a_text_that_is_no_one_note(case, text):
    with pytest.raises(ValueError):
        service.check_note_draft(case, text)
