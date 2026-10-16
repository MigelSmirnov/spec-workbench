"""The notes gate hands the note addresses of a standard_version 3 case to the
Factory's resolver (SPEC_STANDARD §15.3.1, Data Closure decision Q5)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import spec_projection_workbench
from notes_workbench import factory_addresses, gate
from questions_workbench import documents as question_documents

# A stand-in for code-factory tools/spec_address.py: one verdict per address,
# `= models.Known` and provider constants legal, everything else closed.
FAKE_RESOLVER = r'''
import json, re, sys
spec = json.load(sys.stdin)
items = []
for index, note in enumerate(spec["notes"]):
    for match in re.finditer(r"=\s*((?:models|rules|config)\.[A-Za-z_.]+[A-Za-z_])", note):
        address = match.group(1)
        legal = address == "models.Known"
        items.append({"note_index": index, "address": address,
                      "status": "legal" if legal else "illegal",
                      "code": "legal" if legal else "address_form_closed",
                      "message": "closed in v3"})
json.dump({"schema_version": "factory_spec_address.v1", "addresses": items}, sys.stdout)
'''


def _project(tmp_path: Path, notes: str, version: int) -> Path:
    project = tmp_path / "case"
    project.mkdir()
    (project / "30_modules.md").write_text("## `module:parser`\n", encoding="utf-8")
    (project / "60_contracts.json").write_text(json.dumps({
        "schema_version": "spec_workbench_state6_contracts.v1",
        "contracts": {"parse": "(raw: str) -> str | None"},
    }), encoding="utf-8")
    (project / "60_data_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_state6_data_closure.v1",
        "placements": [{"address": "rules.parser.parse_policy"}],
    }), encoding="utf-8")
    (project / "global_spec.json").write_text(json.dumps({"standard_version": version}), encoding="utf-8")
    (project / "80_notes.md").write_text(notes, encoding="utf-8")
    return project


@pytest.fixture
def factory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "factory"
    (root / "tools").mkdir(parents=True)
    (root / "tools/spec_address.py").write_text(FAKE_RESOLVER, encoding="utf-8")
    monkeypatch.setenv(question_documents.FACTORY_ROOT_ENV, str(root))
    monkeypatch.setattr(spec_projection_workbench, "projected_spec",
                        lambda project: {"standard_version": 3, "models": {}, "rules": {}})
    return root


def _blocks(report: dict) -> list[tuple[str, int | None]]:
    return [(item["code"], item.get("line")) for item in report["findings"] if item["severity"] == "block"]


NOTES = (
    "parse: [BEHAVIOR] MUST return = models.Known.\n"
    "parse: [RULE_REFERENCE] MUST apply = rules.parser.parse_policy before returning.\n"
)


def test_a_v2_case_keeps_the_gates_own_address_checks(tmp_path: Path, factory: Path) -> None:
    report = gate.coverage(_project(tmp_path, NOTES, 2))
    # models.Known is unknown to the v2 index; the rules address resolves there
    assert _blocks(report) == [("unresolved_structured_reference", 1)]


def test_a_v3_case_is_judged_by_the_factory_resolver_on_the_authored_line(
    tmp_path: Path, factory: Path
) -> None:
    report = gate.coverage(_project(tmp_path, NOTES, 3))
    assert sorted(_blocks(report)) == [("address_form_closed", 2), ("note_class_closed", 2)]
    closed = next(item for item in report["findings"] if item["code"] == "address_form_closed")
    assert closed["scope"] == "parse" and closed["message"].startswith("rules.parser.parse_policy")


def test_a_v3_case_without_a_factory_blocks(tmp_path: Path, factory: Path, monkeypatch) -> None:
    monkeypatch.setenv(question_documents.FACTORY_ROOT_ENV, str(tmp_path / "nowhere"))
    report = gate.coverage(_project(tmp_path, "parse: [BEHAVIOR] MUST return = models.Known.\n", 3))
    assert _blocks(report) == [("note_address_resolver_unavailable", None)]


def test_a_v3_case_that_does_not_project_blocks(tmp_path: Path, factory: Path, monkeypatch) -> None:
    def broken(project):
        raise ValueError("no sequence")

    monkeypatch.setattr(spec_projection_workbench, "projected_spec", broken)
    report = gate.coverage(_project(tmp_path, "parse: [BEHAVIOR] MUST return = models.Known.\n", 3))
    assert _blocks(report) == [("note_address_projection_failed", None)]


def test_a_resolver_without_a_report_blocks(tmp_path: Path, factory: Path) -> None:
    (factory / "tools/spec_address.py").write_text("raise SystemExit(2)\n", encoding="utf-8")
    report = gate.coverage(_project(tmp_path, "parse: [BEHAVIOR] MUST return = models.Known.\n", 3))
    assert _blocks(report) == [("note_address_resolver_failed", None)]


def test_the_real_factory_resolver_answers_the_gates_input(tmp_path: Path, monkeypatch) -> None:
    root = question_documents.factory_root()
    version = root / "tools/spec_version.py" if root else None
    if version is None or "NOTE_ADDRESSES_CLOSED_MIN_VERSION" not in version.read_text(encoding="utf-8"):
        pytest.skip("no Factory checkout that closes note addresses (code-factory #87)")
    monkeypatch.setattr(spec_projection_workbench, "projected_spec", lambda project: {
        "standard_version": 3,
        "models": {"Known": {"kind": "enum", "values": ["a", "b"]}},
        "rules": {"data_provider_backend": {"kind": "data_provider_backend",
                                            "constants": {"LIMIT": {"value_type": "positive_integer", "value": 3}}}},
    })
    notes = [
        {"line": 1, "scope": "parse", "class": "BEHAVIOR",
         "text": "MUST return = models.Known under the imported LIMIT constant."},
        {"line": 2, "scope": "parse", "class": "BEHAVIOR",
         "text": "MUST read = rules.data_provider_backend.constants.LIMIT."},
    ]
    findings = factory_addresses.findings(_project(tmp_path, "", 3), notes, factory_root=root)
    assert [(item["code"], item["line"]) for item in findings] == [("address_form_closed", 2)]
