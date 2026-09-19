from __future__ import annotations

import json

from assembly_workbench.model import CHECK_ORDER
from model_surface_workbench import attributes, fields
from model_surface_workbench.index import ModelIndex
from notes_workbench import gate


def _write(tmp_path, *, models_md=None, closure=None, contracts=None, modules=None, notes=None):
    if models_md is not None:
        (tmp_path / "01_models_core.md").write_text(models_md, encoding="utf-8")
    if closure is not None:
        (tmp_path / "60_model_closure_domain.json").write_text(json.dumps({
            "schema_version": "spec_workbench_model_closure.v1", "status": "closed", "models": closure,
        }), encoding="utf-8")
    if contracts is not None:
        (tmp_path / "60_contracts.json").write_text(json.dumps({
            "schema_version": "spec_workbench_state6_contracts.v1", "contracts": contracts,
        }), encoding="utf-8")
    if modules is not None:
        (tmp_path / "30_modules.md").write_text(modules, encoding="utf-8")
    if notes is not None:
        (tmp_path / "80_notes.md").write_text(notes, encoding="utf-8")
    return tmp_path


TYPED_MD = (
    "## Model M01 — Totals\n\n### Meaning\n\nMoney.\n\nCandidate fields:\n\n"
    "- `net: Decimal`;\n- `gross: Decimal`;\n\n### Identity\n\nvalue\n\n"
    "## Model M02 — Pin\n\n### Meaning\n\nSelector.\n\nCandidate fields:\n\n"
    "- `snapshot_sha256: str`;\n- `repository_commit: str`;\n\n### Identity\n\nvalue\n\n"
    "## Model M03 — Legacy\n\n### Meaning\n\nOld.\n\nCandidate fields:\n\n"
    "- `effect_id` and caller-scoped identity;\n- status from the closed set;\n\n### Identity\n\nentity\n"
)
CLOSURE = {
    "Totals": {"identity": "value", "fields": {"net": "Decimal", "gross": "Decimal"}},
    "Pin": {"identity": "value", "fields": {"repository_commit": "str"}},
    "Legacy": {"identity": "entity", "fields": {"effect_id": "str", "status": "str"}},
}


def _codes(items):
    return [item["code"] for item in items]


def test_fields_reports_design_only_field_and_skips_prose_lists(tmp_path):
    report = fields.lint(_write(tmp_path, models_md=TYPED_MD, closure=CLOSURE))
    assert _codes(report["findings"]) == ["model_field_missing_in_closure"]
    finding = report["findings"][0]
    assert finding["model"] == "Pin" and finding["field"] == "snapshot_sha256"
    assert report["summary"] == {
        "models_designed": 3, "models_compared": 2, "models_unparsed": 1,
        "closure_files": ["60_model_closure_domain.json"], "errors": 1, "handoff_ready": False,
    }
    assert report["unparsed_models"] == ["Legacy"]


def test_fields_reports_closure_only_field_type_drift_and_missing_model(tmp_path):
    closure = {
        "Totals": {"identity": "value", "fields": {"net": "int", "gross": "Decimal", "tax": "Decimal"}},
        "Legacy": {"identity": "entity", "fields": {}},
    }
    report = fields.lint(_write(tmp_path, models_md=TYPED_MD, closure=closure))
    assert sorted(_codes(report["findings"])) == [
        "model_field_type_drift", "model_field_undeclared_in_design", "model_missing_in_closure",
    ]


def test_fields_is_ready_when_design_and_closure_agree(tmp_path):
    closure = dict(CLOSURE)
    closure["Pin"] = {"identity": "value", "fields": {"snapshot_sha256": "str", "repository_commit": "str"}}
    report = fields.lint(_write(tmp_path, models_md=TYPED_MD, closure=closure))
    assert report["findings"] == [] and report["summary"]["handoff_ready"] is True


ATTR_CLOSURE = {
    "Totals": {"identity": "value", "fields": {"net": "Decimal", "gross": "Decimal"}},
    "Invoice": {"identity": "entity", "fields": {"id": "str", "totals": "Totals", "supplier": "Party | None"}},
    "Party": {"identity": "value", "fields": {"tax_id": "str | None"}},
    "Candidate": {"identity": "value", "fields": {"invoice": "Invoice"}},
    "Revision": {"identity": "value", "fields": {"canonical_json": "str"}},
    "Reference": {"identity": "value", "fields": {"content_hash": "str"}},
    "Kind": {"kind": "enum", "values": ["a", "b"]},
    "EstimateItemSnapshot": {"identity": "value", "fields": {"unit_price": "Decimal"}},
}
ATTR_CONTRACTS = {
    "validate": "(validator: Validator, candidate: Candidate) -> Invoice",
    "Validator.__init__": "(self, catalogue: Catalogue, settings: Settings) -> None",
    "Validator.run": "(self, candidate: Candidate) -> Invoice",
    "Catalogue.__init__": "(self, settings: Settings) -> None",
}


def _attr_findings(tmp_path, notes: str):
    project = _write(tmp_path, closure=ATTR_CLOSURE, contracts=ATTR_CONTRACTS,
                     modules="## `module:catalogue`\n## `runtime_settings`\n", notes=notes)
    index = ModelIndex.load(project)
    parsed = [{"line": n, "scope": line.split(":")[0], "text": line.split("] ", 1)[1]}
              for n, line in enumerate(notes.splitlines(), start=1) if line.strip()]
    return attributes.findings(parsed, index)


def test_attribute_on_parameter_chain_is_checked(tmp_path):
    found = _attr_findings(tmp_path, "validate: [ORCHESTRATION] MUST read candidate.invoice.totals.gross_total once.\n")
    assert [f["code"] for f in found] == ["note_attribute_unknown"]
    assert found[0]["type"] == "Totals" and found[0]["attribute"] == "gross_total"
    assert found[0]["expression"] == "candidate.invoice.totals.gross_total"
    assert "bound via parameter" in found[0]["message"]


def test_attribute_chain_through_optional_and_declared_fields_passes(tmp_path):
    found = _attr_findings(tmp_path, "validate: [ORCHESTRATION] MUST compare candidate.invoice.supplier.tax_id and candidate.invoice.totals.gross.\n")
    assert found == []


def test_bare_noun_binds_to_field_types_and_class_nouns(tmp_path):
    # totals: only Totals carries the noun -> gross_total is a defect
    found = _attr_findings(tmp_path, "validate: [ORCHESTRATION] MUST use totals.gross_total.\n")
    assert [f["attribute"] for f in found] == ["gross_total"]
    assert found[0]["candidates"] == ["Totals"]
    # revision: Revision (class noun) accepts canonical_json even though no field is named revision
    assert _attr_findings(tmp_path, "validate: [ORCHESTRATION] MUST load the revision and parse revision.canonical_json.\n") == []
    # item: EstimateItemSnapshot carries the noun as a segment
    assert _attr_findings(tmp_path, "validate: [BEHAVIOR] MUST weigh item.unit_price.\n") == []
    # an unknown noun is not judged
    assert _attr_findings(tmp_path, "validate: [BEHAVIOR] MUST honour widget.frobnicate.\n") == []


def test_self_binds_to_init_parameters_and_methods(tmp_path):
    assert _attr_findings(tmp_path, "Validator.run: [ORCHESTRATION] MUST read self.settings and self.catalogue.settings once.\n") == []
    found = _attr_findings(tmp_path, "Validator.run: [ORCHESTRATION] MUST read self.clock.\n")
    assert [f["type"] for f in found] == ["Validator"]


def test_enum_pydantic_api_modules_addresses_and_extensions_are_not_findings(tmp_path):
    notes = (
        "validate: [BEHAVIOR] MUST return Kind.A from = models.Kind.\n"
        "validate: [BEHAVIOR] MUST call Invoice.model_validate_json on candidate.invoice.model_dump_json.\n"
        "validate: [BEHAVIOR] MUST call catalogue.search and `capability:runtime_settings.load_runtime_settings` once.\n"
        "validate: [BEHAVIOR] MUST write snapshot.json, i.e. the file, and json.dumps it.\n"
    )
    assert _attr_findings(tmp_path, notes) == []


def test_empty_index_reports_nothing(tmp_path):
    project = _write(tmp_path, notes="validate: [BEHAVIOR] MUST read totals.gross_total.\n")
    assert attributes.findings([{"line": 1, "scope": "validate", "text": "MUST read totals.gross_total."}], ModelIndex.load(project)) == []


def test_notes_gate_blocks_unknown_attribute(tmp_path):
    project = _write(
        tmp_path, closure=ATTR_CLOSURE, contracts={"validate": ATTR_CONTRACTS["validate"]},
        modules="## `module:validation`\n",
        notes="validate: [ORCHESTRATION] MUST use candidate.invoice.totals.gross_total once.\n",
    )
    (tmp_path / "60_data_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_state6_data_closure.v1", "placements": [],
    }), encoding="utf-8")
    report = gate.coverage(project)
    codes = {item["code"] for item in report["findings"]}
    assert "note_attribute_unknown" in codes
    assert report["summary"]["handoff_ready"] is False


def test_fields_is_an_assembly_check_after_identity():
    assert CHECK_ORDER.index("fields") == CHECK_ORDER.index("identity") + 1
