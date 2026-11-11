"""record_construction_backend/v1 (SPEC_STANDARD §6.13): the State 6 closure gate.

The fixtures are byte-identical to the Factory's
``verification/fixtures/record_construction``; MANIFEST.json pins each file's
sha256 in both repositories, so the two checkers judge the same bytes.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

import design_authoring_next
import design_record_construction as rc
from spec_projection_workbench import service as projection
from standard_backends import STANDARD_BACKENDS

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "record_construction"
FIXTURE_FILES = sorted(path for path in FIXTURES.glob("*.json") if path.name != "MANIFEST.json")


def _codes(report: dict) -> list[str]:
    return sorted({row["code"] for row in report["findings"]})


def test_manifest_pins_every_fixture_byte_for_byte() -> None:
    manifest = json.loads((FIXTURES / "MANIFEST.json").read_text(encoding="utf-8"))
    assert manifest["schema_version"] == "record_construction_fixtures.v1"
    actual = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in FIXTURE_FILES}
    assert actual == manifest["fixtures"]
    assert {name.split("_")[1] for name in actual if name.startswith("reject_")} == set(rc.CODES)


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda path: path.name)
def test_fixture_gives_exactly_its_code(path: Path) -> None:
    expected = [] if path.name.startswith("accept_") else [path.name.split("_")[1]]
    assert _codes(rc.spec_report(path)) == expected


def test_no_clock_source_in_version_1() -> None:
    assert "clock" not in rc.REF_CELLS
    spec = rc.loads_closed((FIXTURES / "accept_reference.json").read_text(encoding="utf-8"))
    fields = spec["rules"][rc.RULE_KEY]["constructions"]["withdraw_expense"]["fields"]
    fields["updated_at"] = {"ref": "clock"}
    assert {code for code, _ in rc.closure_findings(spec)} == {"RC001"}


def test_determinism_follows_fresh_id_through_called_builders() -> None:
    spec = rc.loads_closed((FIXTURES / "accept_reference.json").read_text(encoding="utf-8"))
    constructions = spec["rules"][rc.RULE_KEY]["constructions"]
    constructions["build_audit_intent"]["fields"]["actor_id"] = {"ref": "fresh_id", "kind": "uuid4"}
    # actor_id is now unused (RC007); determinism is wrong for both builders
    assert {code for code, _ in rc.closure_findings(spec)} == {"RC007", "RC013"}
    flagged = [message for code, message in rc.closure_findings(spec) if code == "RC013"]
    assert any("build_audit_intent" in m for m in flagged) and any("build_creation_audit" in m for m in flagged)


def test_enum_member_names_mirror_the_factory_models_emitter() -> None:
    names = rc.emitted_enum_member_names("AuditAction", {"kind": "enum", "values": ["expense.create", "ok", "class"]})
    assert names == ["EXPENSE_CREATE", "ok", "OK", "CLASS"]


# --- the case gate ---------------------------------------------------------------------------


def _case(tmp_path: Path, monkeypatch, *, status: str = "closed", imports: bool = True) -> tuple[Path, dict]:
    spec = rc.loads_closed((FIXTURES / "accept_reference.json").read_text(encoding="utf-8"))
    backend = spec["rules"].pop(rc.RULE_KEY)
    monkeypatch.setattr(projection, "projected_spec", lambda project: copy.deepcopy(spec))
    (tmp_path / rc.CLOSURE_FILE).write_text(json.dumps({
        "schema_version": rc.CLOSURE_SCHEMA,
        "status": status,
        "source_refs": ["10_models.md", "60_contracts.json"],
        "rationale": "fixture",
        "backend_ir": backend,
    }, indent=1), encoding="utf-8")
    if imports:
        (tmp_path / rc.IMPORTS_FILE).write_text("{}\n", encoding="utf-8")
    return tmp_path, backend


def test_case_without_closure_does_not_use_the_backend(tmp_path) -> None:
    summary = rc.coverage(tmp_path)["summary"]
    assert summary["enabled"] is False and summary["handoff_ready"] is True


def test_closed_case_closure_is_ready(tmp_path, monkeypatch) -> None:
    project, _ = _case(tmp_path, monkeypatch)
    report = rc.coverage(project)
    assert report["findings"] == [] and report["summary"]["handoff_ready"] is True
    assert rc.main([str(project), "--coverage"]) == 0


def test_open_closure_is_not_ready(tmp_path, monkeypatch) -> None:
    project, _ = _case(tmp_path, monkeypatch, status="open")
    summary = rc.coverage(project)["summary"]
    assert summary["blocks"] == 0 and summary["handoff_ready"] is False


def test_case_finding_blocks(tmp_path, monkeypatch) -> None:
    project, backend = _case(tmp_path, monkeypatch)
    backend["constructions"]["withdraw_expense"]["fields"]["status"]["member"] = "ARCHIVED"
    closure = json.loads((project / rc.CLOSURE_FILE).read_text(encoding="utf-8"))
    closure["backend_ir"] = backend
    (project / rc.CLOSURE_FILE).write_text(json.dumps(closure), encoding="utf-8")
    report = rc.coverage(project)
    assert _codes(report) == ["RC009"] and report["summary"]["blocks"] == 1
    assert rc.main([str(project), "--coverage"]) == 1


def test_import_edges_are_carried_until_the_imports_closure_exists(tmp_path, monkeypatch) -> None:
    spec = rc.loads_closed((FIXTURES / "reject_RC014_import_edges.json").read_text(encoding="utf-8"))
    backend = spec["rules"].pop(rc.RULE_KEY)
    monkeypatch.setattr(projection, "projected_spec", lambda project: copy.deepcopy(spec))
    (tmp_path / rc.CLOSURE_FILE).write_text(json.dumps({
        "schema_version": rc.CLOSURE_SCHEMA, "status": "closed", "source_refs": [], "rationale": "x",
        "backend_ir": backend,
    }), encoding="utf-8")
    carried = rc.coverage(tmp_path)["summary"]
    assert (carried["carried"], carried["blocks"], carried["handoff_ready"]) == (1, 0, True)
    (tmp_path / rc.IMPORTS_FILE).write_text("{}\n", encoding="utf-8")
    blocked = rc.coverage(tmp_path)["summary"]
    assert (blocked["carried"], blocked["blocks"], blocked["handoff_ready"]) == (0, 1, False)


def test_duplicate_key_in_the_closure_file_is_rc003(tmp_path) -> None:
    text = (FIXTURES / "reject_RC003_duplicate_key.json").read_text(encoding="utf-8")
    ir = text[text.index('"record_construction_backend": ') + len('"record_construction_backend": '):]
    (tmp_path / rc.CLOSURE_FILE).write_text(
        '{"schema_version": "%s", "status": "closed", "source_refs": [], "rationale": "x",\n "backend_ir": %s'
        % (rc.CLOSURE_SCHEMA, ir.rstrip().rstrip("}").rstrip().rstrip("}") + "}}"),
        encoding="utf-8",
    )
    assert _codes(rc.coverage(tmp_path)) == ["RC003"]


# --- the sequence, the standard backend, the projection ---------------------------------------


def test_authoring_next_stops_at_an_unclosed_record_construction(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)
    monkeypatch.setattr(design_authoring_next, "_transition_stop", lambda *args: None)
    for name in (design_authoring_next.design_stage6_data.DEFAULT_FILE,
                 design_authoring_next.design_stage6_contracts.DEFAULT_PLAN_FILE,
                 design_authoring_next.design_stage6_contracts.DEFAULT_CATALOG_FILE):
        (tmp_path / name).write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: {"summary": {"errors": 0}})
    monkeypatch.setattr(design_authoring_next.design_stage6_contracts, "handoff",
                        lambda project: {"ready": True, "summary": {}, "unresolved_functions": []})
    _case(tmp_path, monkeypatch, status="open")
    report = design_authoring_next.next_step(tmp_path)
    assert report["phase"] == "deterministic_record_construction_closure"
    assert report["blocked"] is False
    assert "design_record_construction.py" in report["action"]["command"]
    assert "--coverage" in report["action"]["args"]
    assert any(doc.get("section", "").startswith("6.13") for doc in report["read"])


def test_standard_backend_scopes_are_the_builders(tmp_path, monkeypatch) -> None:
    _, backend = _case(tmp_path, monkeypatch)
    standard = next(item for item in STANDARD_BACKENDS if item.id == "record_construction")
    assert (standard.closure_file, standard.closure_schema, standard.rule_key, standard.scope_mapping_path) == (
        rc.CLOSURE_FILE, rc.CLOSURE_SCHEMA, rc.RULE_KEY, ("constructions",))
    assert standard.deterministic_method_scopes(tmp_path) == set(backend["constructions"])
    assert standard.module_slice(tmp_path, "record_builders")["backend_ir"] == backend
    assert standard.module_slice(tmp_path, "expense_intake") is None
    assert f"rules.{rc.RULE_KEY}.constructions.withdraw_expense" in standard.structured_addresses(tmp_path)
