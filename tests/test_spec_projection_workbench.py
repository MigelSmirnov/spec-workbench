from __future__ import annotations

import json

import pytest

from spec_projection_workbench import service
from spec_projection_workbench.model import SpecProjectionError


def _project(tmp_path):
    root = tmp_path
    project = root / "examples" / "case"
    project.mkdir(parents=True)
    sequence_dir = root / "skills" / "spec-authoring"
    sequence_dir.mkdir(parents=True)
    (sequence_dir / "authoring_sequence.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_authoring_sequence.v2",
                "phases": [
                    {
                        "id": "deterministic_persistence_closure",
                        "compatibility_artifacts": ["70_persistence_closure.json"],
                    },
                    {
                        "id": "deterministic_http_router_closure",
                        "compatibility_artifacts": ["70_router_closure.json"],
                    },
                    {
                        "id": "deterministic_http_router_context_closure",
                        "compatibility_artifacts": ["70_router_context.json"],
                    },
                ],
                "invariants": {
                    "persistence_final_ir_is_deterministic_projection": True,
                    "router_final_ir_is_deterministic_projection": True,
                },
            }
        ),
        encoding="utf-8",
    )
    current = {
        "standard_version": 2,
        "config": {"old": True},
        "contracts": {"old": "() -> None", "OldType.run": "(self) -> None"},
        "rules": {
            "legacy_policy": {"old": True},
            "source_byte_store_backend": {"kind": "source_byte_store_backend"},
        },
        "persistence": {},
        "properties": {},
        "determinism": {},
        "module_functions": {
            "alpha": ["old", "OldType", "KeepError"],
            "models": [],
        },
        "imports": {"stdlib": [], "third_party": [], "internal": {"models": []}},
        "function_order": ["old", "OldType.run"],
    }
    (project / "global_spec.json").write_text(
        json.dumps(current, indent=2) + "\n", encoding="utf-8"
    )
    # the imports closure owns imports.module_internal (IMPORTS_WORKBENCH.md §4)
    (project / "65_imports.json").write_text(
        json.dumps({"schema_version": "spec_workbench_imports.v1", "scopes": {}}) + "\n", encoding="utf-8"
    )
    return project


def _patch_ready_sources(monkeypatch):
    data = {
        "status": "accepted",
        "sections": {
            "config": {"new": 1},
            "rules": {"policy": {"mode": "strict"}},
            "persistence": {"Record": {"class": "master"}},
            "properties": {"stable": True},
            "determinism": {"ordering": "stable"},
        },
    }
    monkeypatch.setattr(
        service.design_stage6_data,
        "lint",
        lambda project: {"summary": {"errors": 0}},
    )
    monkeypatch.setattr(service.design_stage6_data, "load", lambda project: data)
    monkeypatch.setattr(service.design_stage6_data, "DEFAULT_FILE", "60_data_closure.json")
    monkeypatch.setattr(
        service.design_stage6_contracts,
        "handoff",
        lambda project: {
            "ready": True,
            "summary": {"errors": 0, "plan_closed": True},
            "contracts": {
                "new": {
                    "module": "module:alpha",
                    "signature": "() -> str",
                },
                "Thing.__init__": {
                    "module": "module:alpha",
                    "signature": "(self) -> None",
                },
                "Thing.run": {
                    "module": "module:alpha",
                    "signature": "(self) -> str",
                },
            },
        },
    )
    monkeypatch.setattr(
        service.design_stage6_contracts, "DEFAULT_CATALOG_FILE", "60_contracts.json"
    )
    monkeypatch.setattr(
        service.persistence_authoring,
        "handoff",
        lambda project: {
            "enabled": True,
            "ready": True,
            "summary": {"closed": True, "errors": 0},
            "backend_ir": {
                "kind": "persistence_backend",
                "schema_version": 3,
            },
        },
    )


def test_plan_projects_registered_surfaces_and_preserves_unowned_rules(
    tmp_path, monkeypatch
) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is True
    assert plan["in_sync"] is False
    assert {row["address"] for row in plan["changes"]} >= {
        "config",
        "contracts",
        "function_order",
        "module_functions",
        "persistence",
        "properties",
        "determinism",
        "rules.policy",
        "rules.persistence_backend",
    }

    _, projected, findings, _ = service._project(project)
    assert findings == []
    assert projected["rules"]["source_byte_store_backend"] == {
        "kind": "source_byte_store_backend"
    }
    assert projected["contracts"] == {
        "new": "() -> str",
        "Thing.__init__": "(self) -> None",
        "Thing.run": "(self) -> str",
    }
    assert projected["function_order"] == ["new", "Thing.__init__", "Thing.run"]
    assert projected["module_functions"]["alpha"] == ["KeepError", "new", "Thing"]


def test_exception_taxonomy_projects_owned_exception(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "60_exception_taxonomy.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_state6_exception_taxonomy.v1",
                "status": "closed",
                "exceptions": [
                    {
                        "symbol": "NotPermittedError",
                        "module": "module:alpha",
                        "meaning": "The actor table rejected the call.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    _, projected, findings, sources = service._project(project)

    assert findings == []
    assert "NotPermittedError" in projected["module_functions"]["alpha"]
    assert "NotPermittedError" in projected["imports"]["internal"]["alpha"]
    assert any(
        row["source"] == "60_exception_taxonomy.json" and row["ready"] is True
        for row in sources
    )


def test_model_closure_projects_new_model_ownership(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["models"] = {"ExistingRecord": {"fields": {"id": "str"}}}
    current["module_functions"]["models"] = ["ExistingRecord"]
    current["imports"]["internal"]["models"] = ["ExistingRecord"]
    (project / "global_spec.json").write_text(
        json.dumps(current, indent=2) + "\n", encoding="utf-8"
    )
    (project / "60_model_closure_runtime.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_model_closure.v1",
                "status": "closed",
                "models": {"NewRecord": {"fields": {"value": "str"}}},
            }
        ),
        encoding="utf-8",
    )
    _patch_ready_sources(monkeypatch)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["models"]["NewRecord"] == {"fields": {"value": "str"}}
    assert projected["module_functions"]["models"] == [
        "ExistingRecord",
        "NewRecord",
    ]
    assert projected["imports"]["internal"]["models"] == [
        "ExistingRecord",
        "NewRecord",
    ]


def test_open_persistence_handoff_blocks_projection(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        service.persistence_authoring,
        "handoff",
        lambda project: {
            "enabled": True,
            "ready": False,
            "summary": {"closed": False, "errors": 0},
            "backend_ir": None,
        },
    )

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert any(
        row["code"] == "persistence_handoff_not_ready" for row in plan["findings"]
    )
    with pytest.raises(SpecProjectionError, match="projection is blocked"):
        service.apply(project)


def test_router_projection_uses_final_router_assembler(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")
    (project / "70_router_closure.json").write_text("{}", encoding="utf-8")
    (project / "70_router_context.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        service.design_router_ir,
        "assemble",
        lambda project: {
            "ready": True,
            "rules": {
                "http_router_backend": {
                    "kind": "http_router_backend",
                    "schema_version": 1,
                }
            },
        },
    )

    _, projected, findings, checks = service._project(project)

    assert findings == []
    assert projected["rules"]["http_router_backend"]["schema_version"] == 1
    assert any(row["source"].startswith("70_router_closure.json") for row in checks)


def test_apply_is_atomic_and_idempotent(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")

    result = service.apply(project)
    verification = service.verify(project)

    assert result["applied_changes"] > 0
    assert verification["ready"] is True
    assert verification["in_sync"] is True
    assert service.build_plan(project)["summary"]["changes"] == 0


def test_missing_authoring_sequence_fails_closed(tmp_path) -> None:
    project = tmp_path / "examples" / "case"
    project.mkdir(parents=True)
    (project / "global_spec.json").write_text("{}", encoding="utf-8")

    with pytest.raises(SpecProjectionError, match="authoring_sequence.json"):
        service.build_plan(project)


_EPOCH_CLOCK = {
    "kind": "system_clock_backend",
    "schema_version": 2,
    "backend": {"emitter": "python_host_epoch_clock_v1"},
    "wiring": {"module": "system_clock", "function": "now", "models_module": "kernel.models"},
    "time": {"policy": "rules.time_source_policy", "read": "per_call"},
}


def _write_clock_closure(project, *, status: str) -> None:
    (project / "70_system_clock_closure.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_system_clock_backend_closure.v1",
                "status": status,
                "backend_ir": _EPOCH_CLOCK,
            }
        ),
        encoding="utf-8",
    )


def test_standard_backend_closure_is_projected_into_rules(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    _write_clock_closure(project, status="closed")

    plan = service.build_plan(project)
    _, projected, findings, source_checks = service._project(project)

    assert findings == []
    assert projected["rules"]["system_clock_backend"] == _EPOCH_CLOCK
    assert "rules.system_clock_backend" in {row["address"] for row in plan["changes"]}
    assert {
        "source": "70_system_clock_closure.json",
        "enabled": True,
        "ready": True,
        "status": "closed",
        "errors": 0,
    } in source_checks


def test_open_standard_backend_closure_blocks_projection(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    _write_clock_closure(project, status="open")

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["standard_backend_closure_not_closed"]
    _, projected, _, _ = service._project(project)
    assert "system_clock_backend" not in projected["rules"]


def test_closed_data_closure_projects_and_keeps_section_envelopes(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["config"] = {"role": "data", "schema_version": 1, "old": True}
    current["models"] = {"schema_version": 1, "ExistingRecord": {"fields": {"id": "str"}}}
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    _patch_ready_sources(monkeypatch)
    closed = dict(service.design_stage6_data.load(project), status="closed")
    monkeypatch.setattr(service.design_stage6_data, "load", lambda project: closed)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["config"] == {"role": "data", "schema_version": 1, "new": 1}
    assert projected["models"]["schema_version"] == 1
    assert "schema_version" not in projected["module_functions"]["models"]
    assert "schema_version" not in projected["imports"]["internal"]["models"]


def test_data_provider_closure_is_projected_into_rules(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    backend = {"kind": "data_provider_backend", "schema_version": 1,
               "wiring": {"module": "data_provider"}, "constants": {}}
    (project / "70_data_provider_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_data_provider_backend_closure.v1",
        "status": "closed", "backend_ir": backend,
    }), encoding="utf-8")

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["rules"]["data_provider_backend"] == backend


# ── kind: enum and `ordered` in the model closure (Q9-a, step B) ─────

DISCLOSURE = ["open", "business_confidential", "personal_data"]


def _enum_codes(tmp_path, monkeypatch, version, model):
    project = _project(tmp_path)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["standard_version"] = version
    current["models"] = {}
    (project / "global_spec.json").write_text(
        json.dumps(current, indent=2) + "\n", encoding="utf-8"
    )
    (project / "60_model_closure_domain.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_model_closure.v1",
                "status": "closed",
                "models": {"DisclosureClass": model},
            }
        ),
        encoding="utf-8",
    )
    _patch_ready_sources(monkeypatch)
    _, projected, findings, _ = service._project(project)
    for row in findings:
        assert row["severity"] == "block"
        assert row["source"] == "60_model_closure_domain.json"
    assert projected["models"]["DisclosureClass"] == model
    return [row["code"] for row in findings]


@pytest.mark.parametrize(
    ("version", "model", "codes"),
    [
        (2, {"kind": "enum", "values": DISCLOSURE}, []),
        (3, {"kind": "enum", "values": DISCLOSURE}, []),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": True}, []),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": False}, ["ordered_must_be_true"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": "yes"}, ["ordered_must_be_true"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": 1}, ["ordered_must_be_true"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": None}, ["ordered_must_be_true"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": []}, ["ordered_must_be_true"]),
        (3, {"fields": {"id": "str"}, "ordered": True}, ["ordered_outside_enum"]),
        (3, {"kind": "mapping", "rows": [], "ordered": True}, ["ordered_outside_enum"]),
        (2, {"kind": "enum", "values": DISCLOSURE, "ordered": True},
         ["ordered_requires_standard_version_3"]),
        (3, {"kind": "enum", "values": []}, ["enum_values_empty"]),
        (3, {"kind": "enum"}, ["enum_values_empty"]),
        (2, {"kind": "enum", "values": ["open", "open"]}, ["enum_values_duplicate"]),
        (3, {"kind": "enum", "values": ["open", "open"]}, ["enum_values_duplicate"]),
        (2, {"kind": "enum", "values": ["open", 1]}, ["enum_values_not_string"]),
        (2, {"kind": "enum", "members": {"OPEN": "open"}}, []),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": True,
             "members": {"OPEN": "open"}}, ["ordered_enum_members_forbidden"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": True,
             "member_names": {"open": "OPEN"}}, ["ordered_enum_member_names_dict_forbidden"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": True,
             "member_names": ["OPEN", "BC", "PD"]}, []),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": True,
             "member_names": ["OPEN", "BC"]}, ["ordered_enum_member_names_length"]),
        (3, {"kind": "enum", "values": DISCLOSURE, "ordered": True,
             "member_names": "OPEN"}, ["ordered_enum_member_names_length"]),
        (3, {"kind": "enum", "values": ["low", "rank", "high"], "ordered": True},
         ["ordered_enum_reserved_member"]),
        (3, {"kind": "enum", "values": ["low", "mid", "high"], "ordered": True,
             "member_names": ["low", "rank", "high"]}, ["ordered_enum_reserved_member"]),
        (3, {"kind": "enum", "values": ["low", "rank", "high"]}, []),
    ],
)
def test_model_closure_enum_declarations_match_the_factory(
    tmp_path, monkeypatch, version, model, codes
) -> None:
    assert _enum_codes(tmp_path, monkeypatch, version, model) == codes


def test_refused_enum_blocks_the_plan(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["models"] = {}
    (project / "global_spec.json").write_text(
        json.dumps(current, indent=2) + "\n", encoding="utf-8"
    )
    (project / "60_model_closure_domain.json").write_text(
        json.dumps(
            {
                "schema_version": "spec_workbench_model_closure.v1",
                "status": "closed",
                "models": {"DisclosureClass": {"kind": "enum", "values": DISCLOSURE, "ordered": True}},
            }
        ),
        encoding="utf-8",
    )
    _patch_ready_sources(monkeypatch)

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["ordered_requires_standard_version_3"]


def test_refused_enum_already_in_the_specification_is_attributed_to_it(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["models"] = {"Legacy": {"kind": "enum", "values": ["a", "a"]}}
    (project / "global_spec.json").write_text(
        json.dumps(current, indent=2) + "\n", encoding="utf-8"
    )
    _patch_ready_sources(monkeypatch)

    _, _, findings, _ = service._project(project)

    assert [(row["code"], row["source"]) for row in findings] == [
        ("enum_values_duplicate", "global_spec.json")
    ]


def test_keyed_file_spool_closure_is_projected_into_rules(tmp_path, monkeypatch) -> None:
    from test_standard_backends import spool_ir, write_spool

    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    write_spool(project, spool_ir())

    plan = service.build_plan(project)
    _, projected, findings, source_checks = service._project(project)

    assert findings == []
    assert projected["rules"]["keyed_file_spool_backend"] == spool_ir()
    assert "rules.keyed_file_spool_backend" in {row["address"] for row in plan["changes"]}
    assert {
        "source": "70_keyed_file_spool_closure.json",
        "enabled": True,
        "ready": True,
        "status": "closed",
        "errors": 0,
    } in source_checks


@pytest.mark.parametrize("malformed", ["open", "no_errors_object"])
def test_malformed_keyed_file_spool_closure_blocks_projection(tmp_path, monkeypatch, malformed) -> None:
    from test_standard_backends import spool_ir, write_spool

    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    backend_ir = spool_ir()
    if malformed == "no_errors_object":
        del backend_ir["errors"]
    write_spool(project, backend_ir, status="open" if malformed == "open" else "closed")

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["standard_backend_closure_not_closed"]
    _, projected, _, _ = service._project(project)
    assert "keyed_file_spool_backend" not in projected["rules"]


def test_sqlite_unit_of_work_closure_is_projected_into_rules(tmp_path, monkeypatch) -> None:
    from test_standard_backends import uow_ir

    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    # the closure is the only authored statement of the IR; contracts stay State 6's
    (project / "70_sqlite_unit_of_work_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_sqlite_unit_of_work_backend_closure.v1",
        "status": "closed",
        "backend_ir": uow_ir(),
    }), encoding="utf-8")

    plan = service.build_plan(project)
    _, projected, findings, source_checks = service._project(project)

    assert findings == []
    assert projected["rules"]["sqlite_unit_of_work_backend"] == uow_ir()
    assert "rules.sqlite_unit_of_work_backend" in {row["address"] for row in plan["changes"]}
    assert {
        "source": "70_sqlite_unit_of_work_closure.json",
        "enabled": True,
        "ready": True,
        "status": "closed",
        "errors": 0,
    } in source_checks


def test_implementation_obligations_survive_the_projection(tmp_path, monkeypatch) -> None:
    """No design artifact owns the section: it is assembly the projection carries unchanged."""
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    spec_path = project / "global_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    obligations = {
        "AuditRepositoryContext": {"disposition": "local",
                                   "implementations": ["PortalTransaction", "SqliteStaffBootstrapStore"]},
    }
    spec["implementation_obligations"] = obligations
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    _, projected, _, _ = service._project(project)

    assert projected["implementation_obligations"] == obligations


@pytest.mark.parametrize("malformed", ["open", "no_wiring"])
def test_malformed_sqlite_unit_of_work_closure_blocks_projection(tmp_path, monkeypatch, malformed) -> None:
    from test_standard_backends import uow_ir

    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    backend_ir = uow_ir()
    if malformed == "no_wiring":
        del backend_ir["wiring"]
    (project / "70_sqlite_unit_of_work_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_sqlite_unit_of_work_backend_closure.v1",
        "status": "open" if malformed == "open" else "closed",
        "backend_ir": backend_ir,
    }), encoding="utf-8")

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["standard_backend_closure_not_closed"]
    _, projected, _, _ = service._project(project)
    assert "sqlite_unit_of_work_backend" not in projected["rules"]


# -- imports.module_internal belongs to the imports closure (IMPORTS_WORKBENCH.md §4) --

def _imports_table(project, scopes):
    (project / "65_imports.json").write_text(json.dumps(
        {"schema_version": "spec_workbench_imports.v1", "scopes": scopes}) + "\n", encoding="utf-8")


def _with_edges(project, edges):
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["imports"]["module_internal"] = edges
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")


def test_module_internal_is_derived_from_the_imports_table(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")
    # alpha is judged by the closure; emitted keeps the edges an emitter writes
    _with_edges(project, {"alpha": {"models": ["Stale"]}, "emitted": {"models": ["Row"]}})
    _imports_table(project, {
        "alpha": {"uses": [], "rejected": []},
        "alpha.new": {"uses": [{"symbol": "Thing", "provider": "models", "as": "creates", "basis": "contract"}],
                      "rejected": []},
    })

    _, projected, findings, _ = service._project(project)

    assert projected["imports"]["module_internal"] == {"alpha": {"models": ["Thing"]}, "emitted": {"models": ["Row"]}}
    assert not [f for f in findings if f["severity"] == "block"]
    service.apply(project)
    assert service.verify(project)["in_sync"] is True


def test_a_hand_edit_of_module_internal_is_drift(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")
    _imports_table(project, {"alpha": {"uses": [], "rejected": []}})
    service.apply(project)
    _with_edges(project, {"alpha": {"models": ["Thing"]}})

    report = service.verify(project)

    assert report["in_sync"] is False
    assert {"address": "imports.module_internal", "action": "replace"} in report["changes"]


def test_without_the_table_projection_blocks_but_the_closure_can_still_read_the_case(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_persistence_closure.json").write_text("{}", encoding="utf-8")
    (project / "65_imports.json").unlink()

    plan = service.build_plan(project)

    assert "imports_table_missing" in {f["code"] for f in plan["findings"]}
    assert plan["ready_to_apply"] is False
    with pytest.raises(service.SpecProjectionError, match="imports_table_missing"):
        service.projected_spec(project)
    assert service.projected_spec(project, imports=False)["contracts"]["new"] == "() -> str"


# SPEC_STANDARD §10: several roots, a root-level module and a leaf that differs
# from the module name are legal layouts (client-portal / 459ac96c uses all three).
_MIXED_PATHS = {"models": "core/models", "api": "api/router", "api_irregular": "api_irregular",
                "runtime_settings": "runtime/settings"}


def test_existing_module_paths_are_taken_as_given() -> None:
    order = list(_MIXED_PATHS)
    contracts = {"f": {"module": "module:api"}, "g": {"module": "module:models"}}
    result_order, result_paths = service._sync_module_topology(order, dict(_MIXED_PATHS), contracts)
    assert result_order == order
    assert result_paths == _MIXED_PATHS


def test_new_module_still_needs_one_deterministic_root() -> None:
    order = list(_MIXED_PATHS)
    contracts = {"f": {"module": "module:fresh_module"}}
    with pytest.raises(SpecProjectionError, match="fresh_module"):
        service._sync_module_topology(order, dict(_MIXED_PATHS), contracts)


def test_new_module_is_placed_under_the_shared_root() -> None:
    paths = {"models": "app/models", "api": "app/api"}
    contracts = {"f": {"module": "module:fresh_module"}}
    order, result = service._sync_module_topology(list(paths), dict(paths), contracts)
    assert order[-1] == "fresh_module"
    assert result["fresh_module"] == "app/fresh_module"


# ── the data provider's module and retired rules namespaces (client-portal, 2026-11-08) ──

_DATA_PROVIDER = {
    "kind": "data_provider_backend", "schema_version": 2,
    "backend": {"emitter": "python_constant_data_v1"},
    "wiring": {"module": "data_provider", "models_module": "core.models"},
    "constants": {"ZETA_LIMIT": {"value_type": "int", "value": 3},
                  "ALPHA_PREFIX": {"value_type": "string", "value": "/api"}},
}


def _with_topology(project, **extra):
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["module_order"] = ["models", "alpha"]
    current["module_paths"] = {"models": "core/models", "alpha": "domain/alpha"}
    current.update(extra)
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")


def _write_data_provider(project, backend=None):
    (project / "70_data_provider_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_data_provider_backend_closure.v1",
        "status": "closed", "backend_ir": backend or _DATA_PROVIDER,
    }), encoding="utf-8")


def test_data_provider_module_is_placed_after_the_models_module(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _with_topology(project)
    _patch_ready_sources(monkeypatch)
    _write_data_provider(project)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["module_order"] == ["models", "data_provider", "alpha"]
    assert projected["module_paths"] == {
        "models": "core/models", "data_provider": "core/data_provider", "alpha": "domain/alpha"}
    # module_functions holds alpha before models; the new module follows models, its predecessor in the order
    assert list(projected["module_functions"]) == ["alpha", "models", "data_provider"]
    assert projected["module_functions"]["data_provider"] == ["ALPHA_PREFIX", "ZETA_LIMIT"]
    assert projected["imports"]["internal"]["data_provider"] == ["ALPHA_PREFIX", "ZETA_LIMIT"]


def test_placed_data_provider_module_keeps_its_place_and_follows_its_constants(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _with_topology(project)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["module_order"] = ["models", "alpha", "data_provider"]
    current["module_paths"]["data_provider"] = "constants/data_provider"
    current["module_functions"]["data_provider"] = ["DROPPED_CONSTANT"]
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    _patch_ready_sources(monkeypatch)
    _write_data_provider(project)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["module_order"] == ["models", "alpha", "data_provider"]
    assert projected["module_paths"]["data_provider"] == "constants/data_provider"
    assert projected["module_functions"]["data_provider"] == ["ALPHA_PREFIX", "ZETA_LIMIT"]


def test_data_provider_projection_is_idempotent(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _with_topology(project)
    _patch_ready_sources(monkeypatch)
    _write_data_provider(project)
    service.apply(project)
    assert service.verify(project)["in_sync"] is True


def test_data_provider_without_a_models_module_path_blocks(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _with_topology(project)
    _patch_ready_sources(monkeypatch)
    _write_data_provider(project, {**_DATA_PROVIDER, "wiring": {"module": "data_provider",
                                                                 "models_module": "elsewhere.models"}})

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["data_provider_module_unplaceable"]


def test_retired_rules_namespace_is_removed_and_an_undeclared_one_kept(tmp_path, monkeypatch) -> None:
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["rules"]["capability_catalog"] = {"kind": "catalog"}
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    data = dict(service.design_stage6_data.load(project))
    data["retired"] = [{"address": "rules.capability_catalog", "reason": "second home of models.Capability",
                        "source_refs": ["test"]}]
    monkeypatch.setattr(service.design_stage6_data, "load", lambda project: data)

    plan = service.build_plan(project)
    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert "capability_catalog" not in projected["rules"]
    assert projected["rules"]["legacy_policy"] == {"old": True}  # never declared, never retired: kept
    assert {"address": "rules.capability_catalog", "action": "remove"} in plan["changes"]


def test_record_construction_closure_is_projected_into_rules(tmp_path, monkeypatch) -> None:
    from pathlib import Path

    fixture = Path(__file__).resolve().parent / "fixtures" / "record_construction" / "accept_reference.json"
    backend = json.loads(fixture.read_text(encoding="utf-8"))["rules"]["record_construction_backend"]
    project = _project(tmp_path)
    _patch_ready_sources(monkeypatch)
    (project / "70_record_construction_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_record_construction_backend_closure.v1",
        "status": "closed",
        "source_refs": ["60_contracts.json"],
        "rationale": "fixture",
        "backend_ir": backend,
    }), encoding="utf-8")

    _, projected, findings, source_checks = service._project(project)

    assert findings == []
    assert projected["rules"]["record_construction_backend"] == backend
    assert any(row["source"] == "70_record_construction_closure.json" and row["ready"] for row in source_checks)


# ── the record builders' module (client-portal migration onto 6.13, 2026-11-08) ──
# Several module roots, as client-portal has: the module must be placed from its
# IR, not from a shared root, and its edges come from the IR (SPEC_STANDARD 6.13).

def _builders_backend(**wiring):
    return {
        "kind": "record_construction_backend", "schema_version": 1,
        "backend": {"emitter": "python_record_builders_v1"},
        "wiring": {"module": "record_builders", "models_module": "core.models", **wiring},
        "constructions": {
            "build_row": {
                "form": "construct", "target": "Row", "consumers": ["alpha"],
                "over": None, "element": None, "base": None,
                "parts": {"tag": {"target": "Tag", "over": None, "element": None,
                                  "fields": {"limit": {"ref": "constant", "symbol": "ZETA_LIMIT"}}}},
                "fields": {"prefix": {"ref": "constant", "symbol": "ALPHA_PREFIX"},
                           "amount": {"ref": "call", "function": "round_amount", "args": ["amount"]},
                           "tag": {"ref": "part", "name": "tag"}},
                "dropped": {},
            },
            # a builder calling a builder of the same IR imports nothing
            "build_rows": {
                "form": "construct", "target": "Rows", "consumers": ["alpha"],
                "over": None, "element": None, "base": None, "parts": {},
                "fields": {"row": {"ref": "call", "function": "build_row", "args": ["amount"]}},
                "dropped": {},
            },
        },
    }


def _write_builders(project, backend=None):
    (project / "70_record_construction_closure.json").write_text(json.dumps({
        "schema_version": "spec_workbench_record_construction_backend_closure.v1",
        "status": "closed", "source_refs": ["test"], "rationale": "test",
        "backend_ir": backend or _builders_backend(),
    }), encoding="utf-8")


def _patch_builder_contracts(monkeypatch):
    contracts = {
        "new": {"module": "module:alpha", "signature": "() -> str"},
        "round_amount": {"module": "module:policy", "signature": "(amount: Decimal) -> Decimal"},
        "build_row": {"module": "module:record_builders", "signature": "(amount: Decimal) -> Row"},
        "build_rows": {"module": "module:record_builders", "signature": "(amount: Decimal) -> Rows"},
    }
    monkeypatch.setattr(service.design_stage6_contracts, "handoff", lambda project: {
        "ready": True, "summary": {"errors": 0, "plan_closed": True}, "contracts": contracts})


def _builders_case(tmp_path, monkeypatch, *, order=("models", "policy", "alpha"), paths=None, edges=None):
    project = _project(tmp_path)
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["module_order"] = list(order)
    current["module_paths"] = paths or {"models": "core/models", "policy": "domain/policy",
                                        "alpha": "application/alpha"}
    current["module_functions"]["policy"] = ["round_amount"]
    if edges is not None:
        current["imports"]["module_internal"] = edges
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
    _patch_ready_sources(monkeypatch)
    _patch_builder_contracts(monkeypatch)
    _write_data_provider(project)
    _write_builders(project)
    return project


def test_builders_module_is_placed_after_its_last_provider_under_several_roots(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    # after data_provider and policy, the modules it imports; before alpha, which imports it
    assert projected["module_order"] == ["models", "data_provider", "policy", "record_builders", "alpha"]
    assert projected["module_paths"] == {
        "models": "core/models", "data_provider": "core/data_provider", "policy": "domain/policy",
        "record_builders": "core/record_builders", "alpha": "application/alpha"}
    assert projected["module_functions"]["record_builders"] == ["build_row", "build_rows"]


def test_builders_module_edges_are_the_ir_constants_and_calls(tmp_path, monkeypatch) -> None:
    # a hand edit of the builders' edges does not survive: the IR states them
    project = _builders_case(tmp_path, monkeypatch, edges={"record_builders": {"models": ["Stale"]}})

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["imports"]["module_internal"] == {
        "record_builders": {"data_provider": ["ALPHA_PREFIX", "ZETA_LIMIT"], "policy": ["round_amount"]}}


def test_builders_module_without_providers_has_no_edges(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    backend = _builders_backend()
    backend["constructions"]["build_row"]["fields"]["prefix"] = {"ref": "literal", "value": True}
    backend["constructions"]["build_row"]["fields"]["amount"] = {"ref": "name", "name": "amount"}
    backend["constructions"]["build_row"]["parts"]["tag"]["fields"]["limit"] = {"ref": "none"}
    _write_builders(project, backend)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    # right after the models module, its only provider
    assert projected["module_order"][:3] == ["models", "record_builders", "data_provider"]
    assert "record_builders" not in projected["imports"]["module_internal"]


def test_placed_builders_module_is_not_duplicated_or_moved(tmp_path, monkeypatch) -> None:
    order = ("models", "data_provider", "policy", "alpha", "record_builders")
    paths = {"models": "core/models", "data_provider": "core/data_provider", "policy": "domain/policy",
             "alpha": "application/alpha", "record_builders": "builders/record_builders"}
    project = _builders_case(tmp_path, monkeypatch, order=order, paths=paths)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["module_order"] == list(order)
    assert projected["module_paths"] == paths


def test_builders_projection_is_idempotent(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    service.apply(project)
    first = (project / "global_spec.json").read_text(encoding="utf-8")
    assert service.verify(project)["in_sync"] is True
    service.apply(project)
    assert (project / "global_spec.json").read_text(encoding="utf-8") == first
    assert json.loads(first)["module_order"].count("record_builders") == 1


def test_builders_module_after_a_consumer_blocks(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch, order=("models", "alpha", "policy"))

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["record_builders_module_unplaceable"]


def test_builders_without_a_models_module_path_blocks(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    _write_builders(project, _builders_backend(models_module="elsewhere.models"))

    plan = service.build_plan(project)

    assert plan["ready_to_apply"] is False
    assert [row["code"] for row in plan["findings"]] == ["record_builders_module_unplaceable"]


def test_backend_placed_module_needs_no_shared_root() -> None:
    contracts = {"f": {"module": "module:record_builders"}}
    order, paths = service._sync_module_topology(
        list(_MIXED_PATHS), dict(_MIXED_PATHS), contracts, frozenset({"record_builders"}))
    assert order == list(_MIXED_PATHS)
    assert paths == _MIXED_PATHS


# ── the builders' import surface (client-portal hand-wrote both, 2026-11-08) ──
# imports.internal[<wiring.module>] is what consumers import, and imports.stdlib
# must bind the stdlib types the builders' contracts name (SPEC_STANDARD 6.13, §7).

def _with_imports(project, **imports):
    current = json.loads((project / "global_spec.json").read_text(encoding="utf-8"))
    current["imports"].update(imports)
    (project / "global_spec.json").write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")


def test_builders_export_surface_is_every_consumed_builder(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)

    _, projected, findings, _ = service._project(project)

    assert findings == []
    internal = projected["imports"]["internal"]
    assert internal["record_builders"] == ["build_row", "build_rows"]
    # a new export surface is appended, as the data provider's is
    assert list(internal)[-1] == "record_builders"


def test_builders_export_surface_replaces_a_hand_edit(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    _with_imports(project, internal={"models": [], "record_builders": ["build_gone"], "alpha": ["new"]})

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert list(projected["imports"]["internal"]) == ["models", "record_builders", "alpha", "data_provider"]
    assert projected["imports"]["internal"]["record_builders"] == ["build_row", "build_rows"]


def test_builders_contract_types_get_a_stdlib_binding(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    # a bare module name binds no type name (§7); the lines already there stay
    _with_imports(project, stdlib=["from __future__ import annotations", "decimal", "import json"])

    plan = service.build_plan(project)
    _, projected, _, _ = service._project(project)

    assert projected["imports"]["stdlib"] == [
        "from __future__ import annotations", "decimal", "import json", "from decimal import Decimal"]
    assert "imports.stdlib" in {row["address"] for row in plan["changes"]}


def test_bound_builder_types_add_no_stdlib_line(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    lines = ["from datetime import date, datetime", "from decimal import Decimal as Decimal"]
    _with_imports(project, stdlib=list(lines))

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["imports"]["stdlib"] == lines


def test_builders_stdlib_lines_group_by_source(tmp_path, monkeypatch) -> None:
    project = _builders_case(tmp_path, monkeypatch)
    contracts = {
        "new": {"module": "module:alpha", "signature": "() -> str"},
        "round_amount": {"module": "module:policy", "signature": "(amount: Decimal) -> Decimal"},
        "build_row": {"module": "module:record_builders",
                      "signature": "(amount: Decimal, at: datetime, extra: dict[str, Any]) -> Row"},
        "build_rows": {"module": "module:record_builders",
                       "signature": "(amount: Decimal, ids: list[UUID], on: date | None) -> Rows"},
    }
    monkeypatch.setattr(service.design_stage6_contracts, "handoff", lambda project: {
        "ready": True, "summary": {"errors": 0, "plan_closed": True}, "contracts": contracts})
    _with_imports(project, stdlib=["from datetime import datetime"])

    _, projected, findings, _ = service._project(project)

    assert findings == []
    assert projected["imports"]["stdlib"] == [
        "from datetime import datetime",
        "from datetime import date",
        "from decimal import Decimal",
        "from typing import Any",
        "from uuid import UUID",
    ]
