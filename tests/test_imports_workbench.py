"""Imports closure (tools/IMPORTS_WORKBENCH.md): one fixture per known hole (§10)."""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

import design_imports
from imports_workbench import factory, service
from imports_workbench.candidates import scope_candidates
from imports_workbench.case import Case, Note
from imports_workbench.model import AVAILABLE, NOT_APPLICABLE, TABLE_SCHEMA, UNAVAILABLE

NO_CODE = {"status": NOT_APPLICABLE, "modules": {}}


def _case(**overrides) -> Case:
    fields = dict(
        project_root="widgets",
        modules=["models", "catalog", "store", "consumer"],
        module_functions={
            "models": ["Widget", "Part", "UsesWidget", "Cardinality", "Shape", "Circle", "Square", "StoreChange"],
            "catalog": ["make_widget", "CATALOG_VERSION", "SANDBOX_TRAPPED_WITHOUT_ARGUMENT"],
            "store": ["record_change"],
            "consumer": ["use_widget", "add_case"],
        },
        exports={
            "models": ["Widget", "Part", "UsesWidget", "Cardinality", "Shape", "Circle", "Square", "StoreChange"],
            "catalog": ["make_widget", "CATALOG_VERSION", "SANDBOX_TRAPPED_WITHOUT_ARGUMENT"],
            "store": ["record_change"],
            "consumer": ["use_widget", "add_case"],
        },
        contracts={
            "make_widget": "(name: str) -> Widget",
            "record_change": "(change: StoreChange) -> None",
            "use_widget": "(value: UsesWidget) -> 'Shape'",
            "add_case": "(name: str) -> None",
        },
        models={
            "Widget": {"fields": {"name": "str", "part": "Part"}},
            "Part": {"fields": {"code": "str"}},
            "UsesWidget": {"fields": {"widget": "Widget", "cardinality": "Cardinality"}},
            "Cardinality": {"kind": "enum", "values": ["one", "many"]},
            "Shape": {"kind": "discriminated_union", "discriminator": "shape_kind", "variants": ["Circle", "Square"]},
            "Circle": {"fields": {"radius": "int"}},
            "Square": {"fields": {"side": "int"}},
            "StoreChange": {"fields": {"name": "str"}},
        },
        notes=[
            Note("use_widget", "MUST compare the cardinality of the value; it never calls make_widget.", "BEHAVIOR"),
            Note("use_widget", "MUST read SANDBOX_TRAPPED_WITHOUT_ARGUMENT and CATALOG_VERSION.", "BEHAVIOR"),
            Note("add_case", "MUST call store.record_change(change) once.", "BEHAVIOR"),
        ],
        knows={"consumer": ["catalog", "store"]},
    )
    fields.update(overrides)
    return Case(**fields)


def _closed_table(case: Case) -> dict:
    """A table every scope of which is decided the way the fixture's code needs."""
    scopes = case.scopes()
    return {"schema_version": TABLE_SCHEMA, "scopes": {
        "consumer": {"basis_sha256": scopes["consumer"].basis_sha256, "uses": [], "rejected": []},
        "consumer.use_widget": {
            "basis_sha256": scopes["consumer.use_widget"].basis_sha256,
            "uses": [
                {"symbol": "UsesWidget", "provider": "models", "as": "annotates", "basis": "contract"},
                {"symbol": "Shape", "provider": "models", "as": "annotates", "basis": "contract"},
                {"symbol": "Cardinality", "provider": "models", "as": "inspects",
                 "basis": "note:consumer.use_widget#1"},
                {"symbol": "CATALOG_VERSION", "provider": "catalog", "as": "reads",
                 "basis": "note:consumer.use_widget#2"},
                {"symbol": "SANDBOX_TRAPPED_WITHOUT_ARGUMENT", "provider": "catalog", "as": "reads",
                 "basis": "note:consumer.use_widget#2"},
            ],
            "rejected": [
                {"symbol": "make_widget", "provider": "catalog", "candidate": "note_mention",
                 "reason": "the note forbids the call"},
                {"symbol": "Widget", "provider": "models", "candidate": "field_name",
                 "reason": "the value's widget is never read"},
                {"symbol": "Circle", "provider": "models", "candidate": "variant",
                 "reason": "the result is returned whole"},
                {"symbol": "Square", "provider": "models", "candidate": "variant",
                 "reason": "the result is returned whole"},
            ],
        },
        "consumer.add_case": {
            "basis_sha256": scopes["consumer.add_case"].basis_sha256,
            "uses": [
                {"symbol": "record_change", "provider": "store", "as": "calls",
                 "basis": "note:consumer.add_case#1"},
                {"symbol": "StoreChange", "provider": "models", "as": "creates",
                 "basis": "note:consumer.add_case#1"},
            ],
            "rejected": [],
        },
        "catalog": {"basis_sha256": scopes["catalog"].basis_sha256, "uses": [], "rejected": []},
        "catalog.make_widget": {
            "basis_sha256": scopes["catalog.make_widget"].basis_sha256,
            "uses": [{"symbol": "Widget", "provider": "models", "as": "creates", "basis": "contract"}],
            "rejected": [],
        },
        "store": {"basis_sha256": scopes["store"].basis_sha256, "uses": [], "rejected": []},
        "store.record_change": {
            "basis_sha256": scopes["store.record_change"].basis_sha256,
            "uses": [{"symbol": "StoreChange", "provider": "models", "as": "annotates", "basis": "contract"}],
            "rejected": [],
        },
    }}


def _codes(report: dict) -> list[str]:
    return [item["code"] for item in report["findings"]]


def _candidates(case: Case, scope_id: str, uses=()) -> dict:
    return {key: c for key, c in scope_candidates(case, case.scopes()[scope_id], uses).items()}


def _code(**modules) -> dict:
    return {"status": AVAILABLE, "modules": modules}


CODE = {
    "catalog": {"models": ["Widget"]},
    "store": {},
    "consumer": {"models": ["Cardinality", "StoreChange", "UsesWidget"],
                 "catalog": ["CATALOG_VERSION", "SANDBOX_TRAPPED_WITHOUT_ARGUMENT"], "store": ["record_change"]},
}


def test_a_closed_table_passes_and_derives_module_internal():
    case = _case()
    report = service.analyze(case, _closed_table(case), _code(**CODE))

    assert _codes(report) == []
    assert report["summary"]["handoff_ready"] and report["summary"]["strict_ready"]
    assert report["derived"]["module_internal"]["consumer"] == {
        "catalog": ["CATALOG_VERSION", "SANDBOX_TRAPPED_WITHOUT_ARGUMENT"],
        "models": ["Cardinality", "Shape", "StoreChange", "UsesWidget"],
        "store": ["record_change"],
    }
    assert report["out_of_scope"] == {
        "models": "the models module is emitted deterministically and imports nothing of the project"}


def test_a_symbol_named_only_in_a_negative_clause_is_a_negative_candidate():
    candidate = _candidates(_case(), "consumer.use_widget")[("make_widget", "catalog")]

    assert candidate.negative and candidate.sources == {"note_mention"}


def test_without_or_never_inside_a_symbol_does_not_make_the_clause_negative():
    candidate = _candidates(_case(), "consumer.use_widget")[("SANDBOX_TRAPPED_WITHOUT_ARGUMENT", "catalog")]

    assert not candidate.negative


def test_a_type_only_in_a_string_annotation_is_a_contract_candidate_and_needs_no_code_use():
    case = _case()
    assert "contract" in _candidates(case, "consumer.use_widget")[("Shape", "models")].sources

    report = service.analyze(case, _closed_table(case), _code(**CODE))   # code never names Shape

    assert "imports_code_unused" not in _codes(report)


def test_an_enum_member_check_without_the_type_in_notes_comes_from_the_field_and_the_code():
    case = _case()
    candidate = _candidates(case, "consumer.use_widget")[("Cardinality", "models")]
    assert candidate.sources == {"field_name"} and candidate.weak_only

    table = _closed_table(case)
    uses = table["scopes"]["consumer.use_widget"]["uses"]
    uses[:] = [row for row in uses if row["symbol"] != "Cardinality"]
    report = service.analyze(case, table, _code(**CODE))
    assert {"imports_candidate_undecided", "imports_code_undeclared"} <= set(_codes(report))

    uses.append({"symbol": "Cardinality", "provider": "models", "as": "inspects", "basis": "code"})
    assert _codes(service.analyze(case, table, _code(**CODE))) == []


def test_union_variants_not_listed_in_fields_are_candidates():
    found = _candidates(_case(), "consumer.use_widget")

    assert found[("Circle", "models")].sources == {"variant"}
    assert found[("Square", "models")].sources == {"variant"}


def test_a_constant_without_parentheses_and_a_call_through_an_attribute_are_candidates():
    case = _case()

    assert _candidates(case, "consumer.use_widget")[("CATALOG_VERSION", "catalog")].sources == {"note_mention"}
    assert _candidates(case, "consumer.add_case")[("record_change", "store")].sources == {"note_call"}


def test_a_callee_brings_its_signature_types():
    case = _case()
    uses = [{"symbol": "record_change", "provider": "store", "as": "calls", "basis": "note:consumer.add_case#1"}]

    assert "contract" in _candidates(case, "consumer.add_case", uses)[("StoreChange", "models")].sources


def test_a_knows_module_without_a_symbol_blocks_until_rejected():
    case = _case(knows={"consumer": ["catalog", "store"], "store": ["catalog"]})
    table = _closed_table(case)

    report = service.analyze(case, table, NO_CODE)
    assert [(i["subject"], i["provider"]) for i in report["findings"] if i["code"] == "imports_knows_uncovered"] \
        == [("store", "catalog")]

    table["scopes"]["store"]["rejected"].append(
        {"symbol": "*", "provider": "catalog", "candidate": "knows", "reason": "stores what it is given"})
    assert _codes(service.analyze(case, table, NO_CODE)) == []


def test_an_unavailable_factory_blocks_when_the_case_has_a_target():
    case = _case(factory_target="widgets")
    report = service.analyze(case, _closed_table(case), {"status": UNAVAILABLE, "reason": "no checkout",
                                                         "modules": {}})

    assert _codes(report) == ["imports_factory_unavailable"]
    assert not report["summary"]["handoff_ready"]


def test_no_target_is_not_applicable_ready_but_not_strict():
    case = _case()
    report = service.analyze(case, _closed_table(case), NO_CODE)

    assert report["summary"]["code_evidence"] == NOT_APPLICABLE
    assert report["summary"]["handoff_ready"] and not report["summary"]["strict_ready"]


def test_factory_evidence_states(tmp_path, monkeypatch):
    monkeypatch.delenv(factory.FACTORY_ROOT_ENV, raising=False)
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    assert factory.evidence(case_dir, None)["status"] == NOT_APPLICABLE
    assert factory.evidence(case_dir, "widgets", tmp_path / "nowhere")["status"] == UNAVAILABLE

    root = tmp_path / "fake_factory"
    (root / "tools" / "slicer").mkdir(parents=True)
    (root / "tools" / "__init__.py").write_text("", encoding="utf-8")
    (root / "tools" / "slicer" / "__init__.py").write_text("", encoding="utf-8")
    (root / "project_index").mkdir()
    (root / "project_index" / "structure.json").write_text(json.dumps(
        {"projects_dir": "projects", "files": {"global_spec": "specs/base/global_spec.json"}}), encoding="utf-8")
    (root / "projects" / "widgets" / "specs" / "base").mkdir(parents=True)
    (root / "projects" / "widgets" / "specs" / "base" / "global_spec.json").write_text("{}", encoding="utf-8")
    main = root / "tools" / "slicer" / "__main__.py"

    main.write_text("print('{\"modules\": {\"consumer\": {}}}')\n", encoding="utf-8")
    old = factory.evidence(case_dir, "widgets", root)
    assert old["status"] == UNAVAILABLE and "predates --code-root" in old["reason"]

    main.write_text("import json, sys\nassert '--code-root' in sys.argv\n"
                    "print(json.dumps({'modules': {'consumer': {'code_imports': {'store': ['record_change']}},"
                    " 'store': {'code_imports': None}}}))\n", encoding="utf-8")
    found = factory.evidence(case_dir, "widgets", root)
    assert found["status"] == AVAILABLE
    assert found["modules"] == {"consumer": {"store": ["record_change"]}, "store": None}


def test_a_module_without_code_keeps_strict_off():
    case = _case()
    code = _code(**{**CODE, "store": None})

    report = service.analyze(case, _closed_table(case), code)

    assert report["summary"]["handoff_ready"] and not report["summary"]["strict_ready"]
    assert report["summary"]["modules_without_code"] == ["store"]


def test_a_manual_edit_of_module_internal_is_drift():
    case = _case()
    table = _closed_table(case)
    case.module_internal = copy.deepcopy(service.derive(table))
    assert service.drift(case, table) == []

    case.module_internal["consumer"]["models"].append("Part")

    assert service.drift(case, table) == [
        {"module": "consumer", "provider": "models", "extra": ["Part"], "missing": []}]


def test_a_contract_change_after_closing_makes_the_scope_stale():
    case = _case()
    table = _closed_table(case)
    case.contracts["add_case"] = "(name: str, count: int) -> None"

    report = service.analyze(case, table, NO_CODE)

    assert [(i["code"], i["subject"]) for i in report["findings"]] == [("imports_scope_stale", "consumer.add_case")]


def test_a_note_change_after_closing_makes_the_scope_stale():
    case = _case()
    table = _closed_table(case)
    case.notes[2] = Note("add_case", "MUST call store.record_change(change) twice.", "BEHAVIOR")

    assert _codes(service.analyze(case, table, NO_CODE)) == ["imports_scope_stale"]


def test_a_weak_candidate_accepted_without_a_note_or_code_basis_blocks():
    case = _case()
    table = _closed_table(case)
    rows = table["scopes"]["consumer.use_widget"]
    rows["rejected"] = [row for row in rows["rejected"] if row["symbol"] != "Circle"]
    rows["uses"].append({"symbol": "Circle", "provider": "models", "as": "inspects", "basis": "author:all of them"})

    assert _codes(service.analyze(case, table, NO_CODE)) == ["imports_weak_without_basis"]


def test_undecided_missing_and_unknown_scopes_block():
    case = _case()
    table = _closed_table(case)
    del table["scopes"]["consumer.add_case"]
    table["scopes"]["consumer.gone"] = {"basis_sha256": "x", "uses": [], "rejected": []}
    table["scopes"]["consumer.use_widget"]["rejected"].pop(0)

    codes = _codes(service.analyze(case, table, NO_CODE))

    # the deleted scope held the module's only use of store, a State 3 Knows collaborator
    assert sorted(codes) == ["imports_candidate_undecided", "imports_knows_uncovered", "imports_scope_missing",
                             "imports_scope_unknown"]
    assert _codes(service.analyze(case, None, NO_CODE)) == ["imports_table_missing"]


def test_uses_resolve_against_the_catalog_and_the_module_order():
    case = _case()
    table = _closed_table(case)
    uses = table["scopes"]["store.record_change"]["uses"]
    uses += [
        {"symbol": "Ghost", "provider": "models", "as": "reads", "basis": "author:x"},
        {"symbol": "Widget", "provider": "catalog", "as": "reads", "basis": "author:x"},
        {"symbol": "use_widget", "provider": "consumer", "as": "calls", "basis": "author:x"},
        {"symbol": "Part", "provider": "models", "as": "teleports", "basis": "author:x"},
        {"symbol": "Part", "provider": "models", "as": "reads", "basis": "note:store.record_change#9"},
    ]

    codes = set(_codes(service.analyze(case, table, NO_CODE)))

    # the accepted call to use_widget also brings its signature types as undecided candidates
    assert codes == {"imports_basis_invalid", "imports_edge_forbidden", "imports_provider_wrong",
                     "imports_symbol_unknown", "imports_use_invalid", "imports_candidate_undecided"}


def test_code_unused_is_closed_by_code_outdated():
    case = _case()
    table = _closed_table(case)
    code = _code(**{**CODE, "consumer": {**CODE["consumer"], "catalog": ["CATALOG_VERSION"]}})

    assert _codes(service.analyze(case, table, code)) == ["imports_code_unused"]

    for row in table["scopes"]["consumer.use_widget"]["uses"]:
        if row["symbol"] == "SANDBOX_TRAPPED_WITHOUT_ARGUMENT":
            row["code_outdated"] = "the code predates the new note"
    report = service.analyze(case, table, code)
    assert _codes(report) == [] and report["summary"]["strict_ready"]


def test_a_code_symbol_can_be_rejected_with_a_reason():
    case = _case()
    table = _closed_table(case)
    code = _code(**{**CODE, "store": {"models": ["Part"]}})
    assert _codes(service.analyze(case, table, code)) == ["imports_code_undeclared"]

    table["scopes"]["store"]["rejected"].append(
        {"symbol": "Part", "provider": "models", "candidate": "code_used", "reason": "dead import in old code"})
    assert _codes(service.analyze(case, table, code)) == []


def test_deterministic_contracts_have_no_scope_and_their_module_is_named():
    case = _case(deterministic={"record_change"})

    assert "store.record_change" not in case.scopes()
    assert case.out_of_scope()["store"] == "every contract is lowered by an emitter from closed IR"


def test_the_draft_accepts_only_the_signature_types_and_keeps_the_rest_pending():
    case = _case(knows={"consumer": ["catalog", "store"]})
    table = service.draft_table(case, None, _code(**{**CODE, "store": {"models": ["Part"]}}))

    use_widget = table["scopes"]["consumer.use_widget"]
    assert {row["symbol"] for row in use_widget["uses"]} == {"UsesWidget", "Shape"}
    assert all(row["basis"] == "contract" for row in use_widget["uses"])
    pending = {row["symbol"]: row for row in use_widget["pending"]}
    assert set(pending) == {"make_widget", "CATALOG_VERSION", "SANDBOX_TRAPPED_WITHOUT_ARGUMENT",
                            "Cardinality", "Circle", "Square"}
    assert pending["make_widget"]["negative"] is True
    assert "code_used" in pending["Cardinality"]["candidates"]   # the code evidence lands on the operation
    assert [row["symbol"] for row in table["scopes"]["store"]["pending"]] == ["Part"]
    module_pending = {(row["symbol"], row["provider"]) for row in table["scopes"]["consumer"]["pending"]}
    # Knows edges, and StoreChange: the code names it, no operation of the draft has it yet
    assert module_pending == {("*", "catalog"), ("*", "store"), ("StoreChange", "models")}

    report = service.analyze(case, table, NO_CODE)
    assert not report["summary"]["handoff_ready"]
    assert report["summary"]["pending"] > 0


def test_the_draft_keeps_decisions_and_is_idempotent():
    case = _case()
    closed = _closed_table(case)

    redrafted = service.draft_table(case, closed, _code(**CODE))

    assert redrafted == service.draft_table(case, redrafted, _code(**CODE))
    assert service.derive(redrafted) == service.derive(closed)
    assert all("pending" not in entry for entry in redrafted["scopes"].values())


def test_cli_reports_input_errors(tmp_path, capsys):
    assert design_imports.main([str(tmp_path / "missing"), "--coverage"]) == 2
    (tmp_path / "65_imports.json").write_text("{", encoding="utf-8")
    with pytest.raises(Exception):
        service.load_table(tmp_path)
