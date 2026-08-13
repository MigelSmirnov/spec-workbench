from __future__ import annotations

import json
import shutil
from pathlib import Path

import design_router_context
import design_router_ir
from router_workbench import authoring


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"
CATALOG = "70_router_closure.json"


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def _catalog(project: Path) -> dict[str, object]:
    return json.loads((project / CATALOG).read_text(encoding="utf-8"))


def _write(project: Path, payload: dict[str, object]) -> None:
    (project / CATALOG).write_text(json.dumps(payload), encoding="utf-8")


def test_current_cabinet_route_catalog_is_contract_aware_ready() -> None:
    report = authoring.coverage(CABINET)
    assert report["summary"] == {
        "external_operations": 13,
        "catalog_items": 13,
        "resolved": 13,
        "unresolved": 0,
        "errors": 0,
        "handoff_ready": True,
    }
    assert report["unresolved_operations"] == []
    assert report["findings"] == []


def test_wrong_handler_is_rejected_against_state6(tmp_path: Path) -> None:
    project = _project(tmp_path)
    payload = _catalog(project)
    table = next(item for item in payload["items"] if item["emission"] == "table")
    table["handler"] = "invented_handler"
    _write(project, payload)
    report = authoring.coverage(project)
    assert report["summary"]["handoff_ready"] is False
    assert any(item["code"] == "handler_contract_mismatch" for item in report["findings"])


def test_wrong_delegate_arity_is_rejected_against_state6(tmp_path: Path) -> None:
    project = _project(tmp_path)
    payload = _catalog(project)
    item = next(item for item in payload["items"] if item["operation"] == "public_op:registry_context.get_assignment_validation")
    item["delegate"]["args"] = [{"ref":"parameter","path":["invoice_id"]}]
    _write(project, payload)
    report = authoring.coverage(project)
    assert report["summary"]["handoff_ready"] is False
    assert any(item["code"] == "delegate_arity_mismatch" for item in report["findings"])


def test_global_router_context_is_ready() -> None:
    report = design_router_context.coverage(CABINET)
    assert report["summary"] == {"errors": 0, "unresolved": 0, "handoff_ready": True}
    assert report["unresolved_topics"] == []
    assert report["findings"] == []


def test_credential_extractor_has_canonical_factory_fields() -> None:
    context = design_router_context.load(CABINET)
    assert context["wiring"]["credential_extractors"]["bearer"] == {
        "kind": "header_scheme",
        "function": "extract_bearer_credential",
        "header": "Authorization",
        "scheme": "Bearer",
        "reject_with": "AuthenticationRequiredError",
    }


def test_final_router_ir_is_deterministically_assembled() -> None:
    handoff = design_router_ir.assemble(CABINET)
    assert handoff["ready"] is True
    ir = handoff["rules"]["http_router_backend"]
    assert ir["kind"] == "http_router_backend"
    assert ir["schema_version"] == 1
    assert ir["backend"] == {"framework": "fastapi", "emitter": "fastapi_sync_v1"}
    assert len(ir["routes"]) == 13
    assert all("operation" not in route for route in ir["routes"])
    assert sum(route["emission"] == "irregular" for route in ir["routes"]) == 1
    irregular = next(route for route in ir["routes"] if route["emission"] == "irregular")
    assert irregular["handler"] == "attach_local_source_handler"
    assert ir["irregular_ownership"] == {"module": "api_irregular"}


def test_assembled_spec_contains_normative_router_ir_without_handoff_wrapper() -> None:
    spec = json.loads((CABINET / "global_spec.json").read_text(encoding="utf-8"))
    handoff = design_router_ir.assemble(CABINET)
    assert spec["rules"]["http_router_backend"] == handoff["rules"]["http_router_backend"]
