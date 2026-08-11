from __future__ import annotations

import json
import shutil
from pathlib import Path

import design_authoring_next
import design_stage6_contracts
from router_workbench.slice import semantic_operation_slice


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"
PLAN = "60_contract_plan.json"
CATALOG = "60_contracts.json"
FIRST_EXTERNAL = "public_op:durable_archive.attach_local_source"


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def _resolve_contracts(project: Path) -> None:
    plan_path = project / PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["status"] = "closed"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    catalog_path = project / CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["contracts"] = {
        entry["function"]: "(value: str) -> str"
        for entry in plan["functions"]
    }
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")


def test_cabinet_state6_contracts_are_open_and_fail_closed() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    assert report["summary"] == {
        "planned_functions": 20,
        "public_functions": 20,
        "internal_functions": 0,
        "resolved": 0,
        "unresolved": 20,
        "errors": 0,
        "plan_closed": False,
        "handoff_ready": False,
    }
    assert len(report["unresolved_functions"]) == 20
    assert any(item["code"] == "contract_plan_open" for item in report["findings"])


def test_next_function_is_deterministic() -> None:
    report = design_stage6_contracts.next_function(CABINET)
    assert report["complete"] is False
    assert report["next"]["function"] == "accept_transfer_manifest"
    assert report["next"]["module"] == "module:durable_archive"
    assert report["next"]["public_operation"] == "public_op:durable_archive.accept_transfer_manifest"


def test_public_operation_mapping_is_complete() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    public_ops = {row["public_operation"] for row in report["functions"] if row["visibility"] == "public"}
    assert len(public_ops) == 20
    assert None not in public_ops
    assert not any(item["code"] == "missing_public_function" for item in report["findings"])


def test_internal_functions_require_explicit_plan_entries(tmp_path: Path) -> None:
    project = _project(tmp_path)
    plan_path = project / PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["functions"].append({
        "function": "_persist_manifest_atomically",
        "module": "module:durable_archive",
        "visibility": "internal",
        "public_operation": None,
        "purpose": "Synthetic explicit internal-function inventory for workbench testing.",
    })
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    report = design_stage6_contracts.coverage(project)
    assert report["summary"]["planned_functions"] == 21
    assert report["summary"]["internal_functions"] == 1
    assert "_persist_manifest_atomically" in report["unresolved_functions"]


def test_closed_resolved_contract_plan_produces_ready_handoff(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _resolve_contracts(project)
    handoff = design_stage6_contracts.handoff(project)
    assert handoff["ready"] is True
    assert handoff["summary"]["handoff_ready"] is True
    assert handoff["summary"]["resolved"] == 20
    assert handoff["unresolved_functions"] == []


def test_authoring_gate_keeps_cabinet_in_state6_before_router() -> None:
    report = design_authoring_next.next_step(CABINET)
    assert report["phase"] == "state6_exact_contracts"
    assert report["blocked"] is False
    assert report["router_allowed"] is False
    assert "design_stage6_contracts.py" in report["next_command"]


def test_authoring_gate_advances_to_router_only_after_contract_handoff(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _resolve_contracts(project)
    report = design_authoring_next.next_step(project)
    assert report["phase"] == "deterministic_http_router_closure"
    assert report["router_allowed"] is True
    assert "design_router_closure.py" in report["next_command"]
    assert report["summary"]["unresolved"] == 11


def test_router_semantic_slice_is_enriched_only_after_contract_handoff(tmp_path: Path) -> None:
    before = semantic_operation_slice(CABINET, FIRST_EXTERNAL)
    assert "canonical_contract" not in before
    project = _project(tmp_path)
    _resolve_contracts(project)
    after = semantic_operation_slice(project, FIRST_EXTERNAL)
    assert after["canonical_contract"]["public_operation"] == FIRST_EXTERNAL
    assert after["canonical_contract"]["signature"] == "(value: str) -> str"
