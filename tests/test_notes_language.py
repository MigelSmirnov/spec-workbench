from __future__ import annotations

import json

from pathlib import Path

from notes_workbench import language

ROOT = Path(__file__).resolve().parents[1]


CREATE_APP = "(archive: DurableArchiveService, plan_actual: PlanActualService) -> FastAPI"


def _project(tmp_path, *, notes, files=None, contracts=None, module_functions=None):
    spec = {
        "module_functions": module_functions or {"parser": ["parse"]},
        "contracts": contracts or {"parse": "(raw: str) -> str | None"},
        "notes": notes,
    }
    (tmp_path / "global_spec.json").write_text(json.dumps(spec), encoding="utf-8")
    for name, body in (files or {}).items():
        (tmp_path / name).write_text(body, encoding="utf-8")
    return tmp_path


def _codes(report):
    return {item["code"] for item in report["findings"]}


def _by_code(report, code):
    return [item for item in report["findings"] if item["code"] == code]


def test_imperative_note_does_not_cover_a_contract(tmp_path):
    project = _project(
        tmp_path,
        notes=["parse: [BEHAVIOR] Return the parsed value without raising."],
    )
    report = language.report(project)

    assert report["status"] == "block"
    finding = _by_code(report, "contract_without_positive_note")[0]
    assert finding["scope"] == "parse"
    assert finding["reason"] == "scoped semantic notes state no positive modal requirement"


def test_modal_note_covers_a_contract(tmp_path):
    project = _project(
        tmp_path,
        notes=["parse: [BEHAVIOR] MUST return the parsed value without raising."],
    )
    report = language.report(project)

    assert report["status"] == "pass"
    assert "contract_without_positive_note" not in _codes(report)


def test_negative_only_note_does_not_cover_a_contract(tmp_path):
    project = _project(
        tmp_path,
        notes=["parse: [FORBIDDEN_ACTION] MUST NOT raise on malformed input."],
    )
    report = language.report(project)

    assert "contract_without_positive_note" in _codes(report)


def test_class_qualified_scope_does_not_cover_the_bare_callable(tmp_path):
    project = _project(
        tmp_path,
        notes=["Parser.parse: [BEHAVIOR] MUST return the parsed value."],
    )
    report = language.report(project)

    finding = _by_code(report, "contract_without_positive_note")[0]
    assert finding["reason"] == "no note is scoped to this callable"


def test_evidence_class_is_not_implementation_semantics(tmp_path):
    project = _project(
        tmp_path,
        notes=["parse: [TEST_EVIDENCE] MUST be covered by a malformed-input case."],
    )
    report = language.report(project)

    finding = _by_code(report, "contract_without_positive_note")[0]
    assert finding["reason"] == "scoped notes carry no semantic note class"


def test_repair_sites_are_reported_for_every_notes_file(tmp_path):
    project = _project(
        tmp_path,
        notes=["parse: [BEHAVIOR] MUST return the parsed value."],
        files={
            "80_notes.md": "parse: [BEHAVIOR] Return the parsed value.\n",
            "80_notes_runtime.md": "- parse [RETURN_SHAPE]: return None on malformed input.\n",
        },
    )
    report = language.report(project)

    sites = {(item["path"], item["line"]) for item in _by_code(report, "note_without_positive_modal")}
    assert sites == {("80_notes.md", 1), ("80_notes_runtime.md", 1)}
    assert report["summary"]["note_files_ungated_by_coverage"] == ["80_notes_runtime.md"]


def test_wrapped_list_note_keeps_its_modal(tmp_path):
    project = _project(
        tmp_path,
        notes=["parse: [BEHAVIOR] MUST return the parsed value."],
        files={
            "80_notes_runtime.md": (
                "- parse [RETURN_SHAPE]: the parser MUST\n"
                "  return None on malformed input.\n"
            ),
        },
    )
    report = language.report(project)

    assert not _by_code(report, "note_without_positive_modal")


def test_dependency_binding_mismatch_is_reported(tmp_path):
    project = _project(
        tmp_path,
        module_functions={"api": ["handle"], "plan": ["calculate"]},
        contracts={
            "create_app": CREATE_APP,
            "handle": "(request: Request) -> None",
            "calculate": "(service: PlanActualService) -> None",
        },
        notes=[
            "handle: [DEPENDENCY_BOUNDARY] MUST obtain the exact DurableArchiveService "
            "bound to request.app.state.archive and pass it to calculate.",
            "calculate: [BEHAVIOR] MUST calculate the analysis.",
        ],
    )
    report = language.report(project)

    finding = _by_code(report, "dependency_binding_mismatch")[0]
    assert finding["bound_type"] == "DurableArchiveService"
    assert finding["required_type"] == "PlanActualService"
    assert finding["delegate"] == "calculate"


def test_consistent_dependency_binding_is_accepted(tmp_path):
    project = _project(
        tmp_path,
        module_functions={"api": ["handle"], "plan": ["calculate"]},
        contracts={
            "create_app": CREATE_APP,
            "handle": "(request: Request) -> None",
            "calculate": "(service: PlanActualService) -> None",
        },
        notes=[
            "handle: [DEPENDENCY_BOUNDARY] MUST obtain the exact PlanActualService "
            "bound to request.app.state.plan_actual and pass it to calculate.",
            "calculate: [BEHAVIOR] MUST calculate the analysis.",
        ],
    )
    report = language.report(project)

    assert report["status"] == "pass"


def test_unbound_app_state_attribute_is_reported(tmp_path):
    project = _project(
        tmp_path,
        module_functions={"api": ["handle"]},
        contracts={"create_app": CREATE_APP, "handle": "(request: Request) -> None"},
        notes=[
            "handle: [DEPENDENCY_BOUNDARY] MUST read request.app.state.registry "
            "before delegating.",
        ],
    )
    report = language.report(project)

    finding = _by_code(report, "unknown_app_state_attribute")[0]
    assert finding["attribute"] == "registry"
    assert finding["bound_attributes"] == ["archive", "plan_actual"]


def test_note_surface_gate_blocks_unknown_attribute_and_undeclared_callable(tmp_path):
    """A note may oblige only what the declared surface carries."""
    import json
    import shutil

    from notes_workbench import language

    case = tmp_path / "cabinet-backend"
    shutil.copytree(ROOT / "examples" / "cabinet-backend", case)
    spec = json.loads((case / "global_spec.json").read_text(encoding="utf-8"))
    owner = {f: m for m, fs in spec["module_functions"].items() for f in fs}

    def model_typed(sig):
        for name, typ in language.signature_parameters(sig):
            model = spec["models"].get(typ.split("|")[0].strip())
            if isinstance(model, dict) and model.get("fields"):
                return name
        return None

    scope, parameter = next(
        (name, model_typed(sig)) for name, sig in spec["contracts"].items()
        if "." not in name and owner.get(name) and model_typed(sig)
    )
    declared = spec["imports"].get("module_internal", {}).get(owner[scope], {})
    foreign = next(
        f for m, fs in spec["module_functions"].items() if m != owner[scope]
        for f in fs if f in spec["contracts"] and "." not in f and f not in declared.get(m, [])
    )
    notes = case / "80_notes.md"
    notes.write_text(
        notes.read_text(encoding="utf-8").rstrip("\n")
        + f"\n{scope}: [BEHAVIOR] MUST read {parameter}.no_such_field before deciding and call {foreign}() afterwards.\n",
        encoding="utf-8",
    )
    findings = language.surface_findings(case, spec)
    codes = {(f["code"], f.get("attribute_path") or f.get("callee")) for f in findings}
    assert ("note_attribute_unknown", f"{parameter}.no_such_field") in codes
    assert any(code == "note_callable_undeclared" and callee == foreign for code, callee in codes)
    assert all(f["severity"] == "block" for f in findings)
    baseline = language.surface_findings(ROOT / "examples" / "cabinet-backend", json.loads((ROOT / "examples" / "cabinet-backend" / "global_spec.json").read_text(encoding="utf-8")))
    assert baseline == []
