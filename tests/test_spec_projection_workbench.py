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
