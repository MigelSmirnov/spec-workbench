from __future__ import annotations

import design_authoring_next


def _ready_data():
    return {"summary": {"errors": 0}}


def _ready_contracts():
    return {"ready": True, "summary": {"handoff_ready": True}, "unresolved_functions": []}


def test_open_persistence_closure_runs_before_router(tmp_path, monkeypatch) -> None:
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
    assert "design_persistence_authoring.py" in report["next_command"]


def test_invalid_persistence_closure_blocks_before_router(tmp_path, monkeypatch) -> None:
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
