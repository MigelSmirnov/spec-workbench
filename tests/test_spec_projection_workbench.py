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
                "schema_version": "spec_workbench_authoring_sequence.v1",
                "intermediate_phases": [
                    {
                        "id": "deterministic_persistence_backend_closure",
                        "compatibility_artifacts": ["70_persistence_closure.json"],
                    },
                    {
                        "id": "deterministic_http_route_closure",
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
