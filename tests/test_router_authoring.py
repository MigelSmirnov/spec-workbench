from __future__ import annotations

import json
import shutil
from pathlib import Path

from decided_reference import decided_reference

import design_router_context
import design_router_ir
from router_workbench import authoring


ROOT = Path(__file__).resolve().parents[1]
CABINET = ROOT / "examples" / "cabinet-backend"
CATALOG = "70_router_closure.json"


def _ready(tmp_path: Path) -> Path:
    return decided_reference(tmp_path)


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "cabinet-backend"
    shutil.copytree(CABINET, project)
    return project


def _catalog(project: Path) -> dict[str, object]:
    return json.loads((project / CATALOG).read_text(encoding="utf-8"))


def _write(project: Path, payload: dict[str, object]) -> None:
    (project / CATALOG).write_text(json.dumps(payload), encoding="utf-8")


def test_current_cabinet_route_catalog_is_contract_aware_ready(tmp_path: Path) -> None:
    CABINET = _ready(tmp_path)
    report = authoring.coverage(CABINET)
    assert report["summary"] == {
        "external_operations": 11,
        "catalog_items": 11,
        "resolved": 11,
        "unresolved": 0,
        "errors": 0,
        "handoff_ready": True,
    }
    assert report["unresolved_operations"] == []
    assert report["findings"] == []


def test_wrong_handler_is_rejected_against_state6(tmp_path: Path) -> None:
    project = _ready(tmp_path)
    payload = _catalog(project)
    table = next(item for item in payload["items"] if item["emission"] == "table")
    table["handler"] = "invented_handler"
    _write(project, payload)
    report = authoring.coverage(project)
    assert report["summary"]["handoff_ready"] is False
    assert any(item["code"] == "handler_contract_mismatch" for item in report["findings"])


def test_wrong_delegate_arity_is_rejected_against_state6(tmp_path: Path) -> None:
    project = _ready(tmp_path)
    payload = _catalog(project)
    item = next(item for item in payload["items"] if item["operation"] == "public_op:registry_context.get_assignment_validation")
    item["delegate"]["args"] = [{"ref":"parameter","path":["invoice_id"]}]
    _write(project, payload)
    report = authoring.coverage(project)
    assert report["summary"]["handoff_ready"] is False
    assert any(item["code"] == "delegate_arity_mismatch" for item in report["findings"])


def test_global_router_context_is_ready(tmp_path: Path) -> None:
    CABINET = _ready(tmp_path)
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


def test_final_router_ir_is_deterministically_assembled(tmp_path: Path) -> None:
    CABINET = _ready(tmp_path)
    handoff = design_router_ir.assemble(CABINET)
    assert handoff["ready"] is True
    ir = handoff["rules"]["http_router_backend"]
    assert ir["kind"] == "http_router_backend"
    assert ir["schema_version"] == 1
    assert ir["backend"] == {"framework": "fastapi", "emitter": "fastapi_sync_v1"}
    assert len(ir["routes"]) == 11
    assert all("operation" not in route for route in ir["routes"])
    assert sum(route["emission"] == "irregular" for route in ir["routes"]) == 1
    irregular = next(route for route in ir["routes"] if route["emission"] == "irregular")
    assert irregular["handler"] == "attach_local_source_handler"
    assert ir["irregular_ownership"] == {"module": "api_irregular"}


def test_assembled_spec_contains_normative_router_ir_without_handoff_wrapper(tmp_path: Path) -> None:
    CABINET = _ready(tmp_path)
    spec = json.loads((CABINET / "global_spec.json").read_text(encoding="utf-8"))
    handoff = design_router_ir.assemble(CABINET)
    assert spec["rules"]["http_router_backend"] == handoff["rules"]["http_router_backend"]


def _answering(tmp_path: Path, mutate=None) -> dict[str, object]:
    project = _ready(tmp_path)
    path = project / "70_router_context.json"
    context = json.loads(path.read_text(encoding="utf-8"))
    contracts = json.loads((project / "60_contracts.json").read_text(encoding="utf-8"))["contracts"]
    answer_function = sorted(contracts)[0]
    context["backend"] = {"framework": "fastapi", "emitter": "fastapi_sync_v2"}
    context["error_policy"] = {
        "body": "answer",
        "default_status": 500,
        "mapping": [{"exception": entry["exception"], "answer": {
            "function": answer_function, "args": [{"ref": "exception", "path": ["code"]}]}}
            for entry in context["error_policy"]["mapping"]],
        "request_validation": {"function": answer_function, "args": [{"ref": "literal", "value": "invalid"}]},
        "unavailable_to_module": context["error_policy"]["unavailable_to_module"],
    }
    if mutate:
        mutate(context)
    path.write_text(json.dumps(context), encoding="utf-8")
    return design_router_context.coverage(project)


def _codes(report: dict[str, object]) -> set[str]:
    return {item["code"] for item in report["findings"]}


def test_fastapi_sync_v2_error_answers_are_accepted(tmp_path: Path) -> None:
    assert _answering(tmp_path)["summary"]["errors"] == 0


def test_error_answers_need_the_v2_emitter(tmp_path: Path) -> None:
    report = _answering(tmp_path, lambda c: c.__setitem__("backend", {"framework": "fastapi", "emitter": "fastapi_sync_v1"}))
    assert "invalid_error_body" in _codes(report)


def test_the_request_validation_answer_has_no_exception_field(tmp_path: Path) -> None:
    report = _answering(tmp_path, lambda c: c["error_policy"]["request_validation"].__setitem__(
        "args", [{"ref": "exception", "path": ["code"]}]))
    assert "invalid_error_answer_ref" in _codes(report)


def test_an_error_answer_names_a_declared_function(tmp_path: Path) -> None:
    report = _answering(tmp_path, lambda c: c["error_policy"]["mapping"][0]["answer"].__setitem__("function", "nowhere"))
    assert "invalid_error_answer" in _codes(report)
