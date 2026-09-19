from __future__ import annotations

import json

import design_authoring_next


def _ready_data():
    return {"summary": {"errors": 0}}


def _ready_contracts():
    return {"ready": True, "summary": {"handoff_ready": True}, "unresolved_functions": []}


def _promoted_states_ready(monkeypatch) -> None:
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)


def _post_state5_files(project) -> None:
    (project / design_authoring_next.design_stage6_data.DEFAULT_FILE).write_text("{}\n", encoding="utf-8")
    (project / design_authoring_next.design_stage6_contracts.DEFAULT_PLAN_FILE).write_text("{}\n", encoding="utf-8")
    (project / design_authoring_next.design_stage6_contracts.DEFAULT_CATALOG_FILE).write_text("{}\n", encoding="utf-8")


def test_open_persistence_closure_runs_before_router(tmp_path, monkeypatch) -> None:
    _promoted_states_ready(monkeypatch)
    _post_state5_files(tmp_path)
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: _ready_data())
    monkeypatch.setattr(design_authoring_next.design_stage6_contracts, "handoff", lambda project: _ready_contracts())
    monkeypatch.setattr(
        design_authoring_next.persistence_authoring,
        "coverage",
        lambda project: {
            "summary": {"handoff_ready": False, "errors": 0, "closed": False},
            "findings": [],
        },
    )
    report = design_authoring_next.next_step(tmp_path)
    assert report["phase"] == "deterministic_persistence_closure"
    assert report["blocked"] is False
    assert "design_persistence_authoring.py" in report["action"]["command"]


def test_invalid_persistence_closure_blocks_before_router(tmp_path, monkeypatch) -> None:
    _promoted_states_ready(monkeypatch)
    _post_state5_files(tmp_path)
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: _ready_data())
    monkeypatch.setattr(design_authoring_next.design_stage6_contracts, "handoff", lambda project: _ready_contracts())
    monkeypatch.setattr(
        design_authoring_next.persistence_authoring,
        "coverage",
        lambda project: {
            "summary": {"handoff_ready": False, "errors": 1, "closed": True},
            "findings": [{"severity": "error", "code": "bad_backend"}],
        },
    )
    report = design_authoring_next.next_step(tmp_path)
    assert report["phase"] == "deterministic_persistence_closure"
    assert report["blocked"] is True


def test_ready_or_absent_persistence_allows_router_phase(tmp_path, monkeypatch) -> None:
    _promoted_states_ready(monkeypatch)
    _post_state5_files(tmp_path)
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: _ready_data())
    monkeypatch.setattr(design_authoring_next.design_stage6_contracts, "handoff", lambda project: _ready_contracts())
    monkeypatch.setattr(
        design_authoring_next.persistence_authoring,
        "coverage",
        lambda project: {
            "summary": {"handoff_ready": True, "errors": 0, "closed": True},
            "findings": [],
        },
    )
    (tmp_path / design_authoring_next.ROUTER_CLOSURE_FILE).write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        design_authoring_next.router_authoring,
        "coverage",
        lambda project: {
            "summary": {"handoff_ready": False, "errors": 0},
            "unresolved_operations": ["public_op:parser.parse"],
        },
    )
    report = design_authoring_next.next_step(tmp_path)
    assert report["phase"] == "deterministic_http_router_closure"
    assert report["persistence_allowed"] is True



def test_missing_data_closure_routes_to_pre_contract_phase(tmp_path, monkeypatch) -> None:
    _promoted_states_ready(monkeypatch)
    report = design_authoring_next.next_step(tmp_path)
    assert report["phase"] == "pre_contract_structured_data_closure"
    assert report["blocked"] is False
    assert report["summary"] == {"closure_exists": False}


def test_missing_state6_plan_and_catalog_route_to_state6_without_crash(tmp_path, monkeypatch) -> None:
    _promoted_states_ready(monkeypatch)
    (tmp_path / design_authoring_next.design_stage6_data.DEFAULT_FILE).write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: _ready_data())

    report = design_authoring_next.next_step(tmp_path)

    assert report["phase"] == "state6_exact_contracts"
    assert report["blocked"] is False
    assert report["summary"] == {"plan_exists": False, "catalog_exists": False}
    assert report["unresolved_functions"] == []


def _ready_through_persistence(tmp_path, monkeypatch) -> None:
    _promoted_states_ready(monkeypatch)
    _post_state5_files(tmp_path)
    monkeypatch.setattr(design_authoring_next.design_stage6_data, "lint", lambda project: _ready_data())
    monkeypatch.setattr(design_authoring_next.design_stage6_contracts, "handoff", lambda project: _ready_contracts())
    monkeypatch.setattr(
        design_authoring_next.persistence_authoring,
        "coverage",
        lambda project: {"summary": {"handoff_ready": True, "errors": 0, "closed": True}, "findings": []},
    )


def test_missing_router_closure_routes_to_router_phase_with_the_external_operations(tmp_path, monkeypatch) -> None:
    _ready_through_persistence(tmp_path, monkeypatch)
    boundary = type("Boundary", (), {"external": ("public_op:surface.run", "public_op:surface.inspect")})()
    monkeypatch.setattr(design_authoring_next, "exposure_boundary", lambda project: boundary)

    report = design_authoring_next.next_step(tmp_path)

    assert report["phase"] == "deterministic_http_router_closure"
    assert report["blocked"] is False
    assert report["summary"] == {"closure_exists": False, "external_operations": 2}
    assert report["unresolved_operations"] == ["public_op:surface.run", "public_op:surface.inspect"]


def test_invalid_router_closure_blocks_without_crash(tmp_path, monkeypatch) -> None:
    _ready_through_persistence(tmp_path, monkeypatch)
    (tmp_path / design_authoring_next.ROUTER_CLOSURE_FILE).write_text("{}\n", encoding="utf-8")

    report = design_authoring_next.next_step(tmp_path)

    assert report["phase"] == "deterministic_http_router_closure"
    assert report["blocked"] is True
    assert report["summary"] == {"closure_exists": True, "errors": 1}


def test_missing_router_context_routes_to_context_phase_without_crash(tmp_path, monkeypatch) -> None:
    _ready_through_persistence(tmp_path, monkeypatch)
    (tmp_path / design_authoring_next.ROUTER_CLOSURE_FILE).write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        design_authoring_next.router_authoring,
        "coverage",
        lambda project: {"summary": {"handoff_ready": True, "errors": 0}, "unresolved_operations": []},
    )

    report = design_authoring_next.next_step(tmp_path)

    assert report["phase"] == "deterministic_http_router_context_closure"
    assert report["blocked"] is False
    assert report["summary"] == {"context_exists": False}


def test_missing_router_closure_with_invalid_exposure_blocks_without_crash(tmp_path, monkeypatch) -> None:
    _ready_through_persistence(tmp_path, monkeypatch)

    report = design_authoring_next.next_step(tmp_path)

    assert report["phase"] == "deterministic_http_router_closure"
    assert report["blocked"] is True
    assert report["summary"] == {"closure_exists": False, "errors": 1}
    assert "exposure" in report["reason"]


def test_the_empty_router_closure_named_by_the_sequencer_is_a_loadable_start(tmp_path, monkeypatch) -> None:
    from router_workbench import catalog

    _ready_through_persistence(tmp_path, monkeypatch)
    boundary = type("Boundary", (), {"external": ("public_op:surface.run",)})()
    monkeypatch.setattr(design_authoring_next, "exposure_boundary", lambda project: boundary)
    reason = design_authoring_next.next_step(tmp_path)["reason"]
    start = reason[reason.index("{"):reason.rindex("}") + 1]

    (tmp_path / design_authoring_next.ROUTER_CLOSURE_FILE).write_text(start, encoding="utf-8")

    assert catalog.load(tmp_path) == {"schema_version": design_authoring_next.ROUTER_CLOSURE_SCHEMA, "items": []}
