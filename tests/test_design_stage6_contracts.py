from __future__ import annotations

import json
import shutil
from pathlib import Path

import design_authoring_next
import design_stage6_contracts
from router_workbench.slice import contract_aware_operation_slice


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"
PLAN = "60_contract_plan.json"
CATALOG = "60_contracts.json"
FIRST_EXTERNAL = "public_op:durable_archive.attach_local_source"


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def _make_unresolved(project: Path, function: str = "attach_local_source") -> None:
    catalog_path = project / CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["contracts"][function] = "unresolved"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")


def test_cabinet_state6_contracts_are_closed_and_ready() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    assert report["summary"] == {
        "planned_functions": 191,
        "public_functions": 35,
        "internal_functions": 156,
        "resolved": 191,
        "unresolved": 0,
        "errors": 0,
        "plan_closed": True,
        "handoff_ready": True,
    }
    assert report["unresolved_functions"] == []
    assert report["findings"] == []


def test_next_function_is_complete_after_state6_handoff() -> None:
    report = design_stage6_contracts.next_function(CABINET)
    assert report["complete"] is True
    assert report["next"] is None
    assert report["summary"]["handoff_ready"] is True


def test_public_operation_mapping_is_complete() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    public_ops = {row["public_operation"] for row in report["functions"] if row["visibility"] == "public"}
    assert len(public_ops) == 35
    assert None not in public_ops
    assert not any(item["code"] == "missing_public_function" for item in report["findings"])


def test_every_external_operation_has_one_canonical_handler_contract() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    handlers = [row for row in report["functions"] if row["router_operation"] is not None]
    assert len(handlers) == 13
    assert len({row["router_operation"] for row in handlers}) == 13
    irregular = [row for row in handlers if row["module"] == "module:api_irregular"]
    assert [row["function"] for row in irregular] == ["attach_local_source_handler"]
    assert irregular[0]["router_operation"] == FIRST_EXTERNAL


def test_internal_functions_require_explicit_plan_entries(tmp_path: Path) -> None:
    project = _project(tmp_path)
    baseline = design_stage6_contracts.coverage(project)["summary"]
    plan_path = project / PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["functions"].append({
        "function": "_persist_manifest_atomically",
        "module": "module:durable_archive",
        "visibility": "internal",
        "purpose": "Synthetic explicit internal-function inventory for workbench testing.",
    })
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    report = design_stage6_contracts.coverage(project)
    assert report["summary"]["planned_functions"] == baseline["planned_functions"] + 1
    assert report["summary"]["internal_functions"] == baseline["internal_functions"] + 1
    assert "_persist_manifest_atomically" in report["unresolved_functions"]
    assert report["summary"]["handoff_ready"] is False


def test_missing_router_handler_mapping_is_fail_closed(tmp_path: Path) -> None:
    project = _project(tmp_path)
    plan_path = project / PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    handler = next(item for item in plan["functions"] if item.get("router_operation") == FIRST_EXTERNAL)
    handler.pop("router_operation")
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    report = design_stage6_contracts.coverage(project)
    assert report["summary"]["handoff_ready"] is False
    assert any(item["code"] == "missing_router_handler_contract" for item in report["findings"])


def test_ready_handoff_contains_operation_and_handler_contracts() -> None:
    handoff = design_stage6_contracts.handoff(CABINET)
    assert handoff["ready"] is True
    assert handoff["summary"]["resolved"] == 191
    domain = handoff["contracts"]["attach_local_source"]
    handler = handoff["contracts"]["attach_local_source_handler"]
    assert domain["public_operation"] == FIRST_EXTERNAL
    assert domain["router_operation"] is None
    assert handler["public_operation"] is None
    assert handler["router_operation"] == FIRST_EXTERNAL


def test_authoring_gate_advances_to_assembly_after_notes_are_closed() -> None:
    report = design_authoring_next.next_step(CABINET)
    assert report["phase"] == "state8_assembly"
    assert report["blocked"] is False
    assert report["router_allowed"] is True
    assert report["next_command"] is None
    assert report["summary"]["handoff_ready"] is True


def test_authoring_gate_returns_to_state6_when_contract_is_unresolved(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _make_unresolved(project)
    report = design_authoring_next.next_step(project)
    assert report["phase"] == "state6_exact_contracts"
    assert report["router_allowed"] is False
    assert "attach_local_source" in report["unresolved_functions"]


def test_router_semantic_slice_contains_both_canonical_contracts() -> None:
    payload = contract_aware_operation_slice(CABINET, FIRST_EXTERNAL)
    assert payload["canonical_contract"]["public_operation"] == FIRST_EXTERNAL
    assert payload["canonical_contract"]["signature"].startswith(
        "(archive: DurableArchiveService, invoice_id: str, files:"
    )
    assert payload["canonical_handler_contract"]["router_operation"] == FIRST_EXTERNAL
    assert payload["canonical_handler_contract"]["signature"] == "(request: Request, invoice_id: str) -> SourceAttachmentBatchResult"
