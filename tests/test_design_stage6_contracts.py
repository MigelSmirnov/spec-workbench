from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from decided_reference import decided_reference

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


def _ready(tmp_path: Path) -> Path:
    return decided_reference(tmp_path)


def _make_unresolved(project: Path, function: str = "attach_local_source") -> None:
    catalog_path = project / CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["contracts"][function] = "unresolved"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")


def test_cabinet_state6_contracts_stop_on_the_undeclared_time_sources() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    assert report["summary"] == {
        "planned_functions": 192,
        "public_functions": 31,
        "internal_functions": 161,
        "resolved": 192,
        "unresolved": 0,
        "errors": 2,
        "plan_closed": True,
        "handoff_ready": False,
    }
    assert report["unresolved_functions"] == []
    # The fence: two mutating operations must produce timestamps and declare
    # no time source. That is a specification decision nobody made, so the
    # reference case stops here until an author decides it (see _ready).
    assert [(f["severity"], f["code"]) for f in report["findings"]] == [
        ("error", "fresh_timestamp_without_source"),
        ("error", "fresh_timestamp_without_source"),
    ]
    assert all(f["hint"].startswith("not decided — decide:") for f in report["findings"])
    ready = design_stage6_contracts.coverage(_ready(Path(tempfile.mkdtemp())))
    assert ready["summary"]["errors"] == 0 and ready["summary"]["handoff_ready"] is True
    assert sorted(f["message"].split(":")[0] for f in report["findings"]) == [
        "lookup_holded_purchase",
        "validate_card_assignment",
    ]


def test_declared_datetime_parameter_clears_time_source_warning(tmp_path: Path) -> None:
    project = _project(tmp_path)
    catalog_path = project / CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    signature = catalog["contracts"]["validate_card_assignment"]
    params, arrow, ret = signature.partition("->")
    catalog["contracts"]["validate_card_assignment"] = f"{params.rstrip().removesuffix(')')}, observed_at: datetime){arrow}{ret}"
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    report = design_stage6_contracts.coverage(project)
    flagged = [f["message"].split(":")[0] for f in report["findings"] if f["code"] == "fresh_timestamp_without_source"]
    assert flagged == ["lookup_holded_purchase"]


def test_next_function_is_complete_after_state6_handoff(tmp_path: Path) -> None:
    report = design_stage6_contracts.next_function(_ready(tmp_path))
    assert report["complete"] is True
    assert report["next"] is None
    assert report["summary"]["handoff_ready"] is True


def test_public_operation_mapping_is_complete() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    public_ops = {row["public_operation"] for row in report["functions"] if row["visibility"] == "public"}
    assert len(public_ops) == 31
    assert None not in public_ops
    assert not any(item["code"] == "missing_public_function" for item in report["findings"])


def test_every_external_operation_has_one_canonical_handler_contract() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    handlers = [row for row in report["functions"] if row["router_operation"] is not None]
    assert len(handlers) == 11
    assert len({row["router_operation"] for row in handlers}) == 11
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


def test_ready_handoff_contains_operation_and_handler_contracts(tmp_path: Path) -> None:
    handoff = design_stage6_contracts.handoff(_ready(tmp_path))
    assert handoff["ready"] is True
    assert handoff["summary"]["resolved"] == 195  # 192 + the decided Clock port and its two retainers
    domain = handoff["contracts"]["attach_local_source"]
    handler = handoff["contracts"]["attach_local_source_handler"]
    assert domain["public_operation"] == FIRST_EXTERNAL
    assert domain["router_operation"] is None
    assert handler["public_operation"] is None
    assert handler["router_operation"] == FIRST_EXTERNAL


def test_authoring_gate_advances_past_contracts_and_notes_to_the_witness_stop(tmp_path: Path, monkeypatch) -> None:
    # The fence: with the time sources decided, State 6 and State 7 no longer
    # stop the case; the next undecided fact is that 21 accepted decisions
    # declare invariants nobody witnesses. The pipeline stops there, with a
    # hint on every finding, instead of advancing to assembly.
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)
    report = design_authoring_next.next_step(_ready(tmp_path))
    assert report["phase"] == "decision_witness_resolution"
    assert report["blocked"] is True
    assert report["router_allowed"] is False
    findings = report["findings"]
    assert findings and {f["code"] for f in findings} == {"decision_without_witness"}
    assert all(f["severity"] == "error" and f["hint"].startswith("not decided — decide:") for f in findings)


def test_authoring_gate_returns_to_state6_when_contract_is_unresolved(tmp_path: Path, monkeypatch) -> None:
    project = _project(tmp_path)
    _make_unresolved(project)
    monkeypatch.setattr(design_authoring_next, "_promoted_states_step", lambda sequence, project, text: None)
    report = design_authoring_next.next_step(project)
    assert report["phase"] == "state6_exact_contracts"
    assert report["router_allowed"] is False
    assert "attach_local_source" in report["unresolved_functions"]


def test_router_semantic_slice_contains_both_canonical_contracts(tmp_path: Path) -> None:
    payload = contract_aware_operation_slice(_ready(tmp_path), FIRST_EXTERNAL)
    assert payload["canonical_contract"]["public_operation"] == FIRST_EXTERNAL
    assert payload["canonical_contract"]["signature"].startswith(
        "(archive: DurableArchiveService, invoice_id: str, files:"
    )
    assert payload["canonical_handler_contract"]["router_operation"] == FIRST_EXTERNAL
    assert payload["canonical_handler_contract"]["signature"] == "(request: Request, invoice_id: str, files: list[UploadFile]) -> SourceAttachmentBatchResult"


def test_module_surface_flags_modules_that_hide_nothing(tmp_path: Path) -> None:
    project = tmp_path / "demo"
    project.mkdir()
    (project / "30_modules.md").write_text(
        """# State 3

## `wide`

### Owns

- x

### Knows

- x

### Must not own

- y

### Depth assessment

kind: deep
hidden mechanism: nothing much

## `gateway`

### Owns

- composition

### Knows

- delegates

### Must not own

- policy

### Depth assessment

kind: facade
delegates to: `wide`
""",
        encoding="utf-8",
    )
    rows = (
        [{"module": "module:wide", "visibility": "public"} for _ in range(6)]
        + [{"module": "module:wide", "visibility": "internal"}]
        + [{"module": "module:gateway", "visibility": "public"} for _ in range(7)]
        + [{"module": "module:narrow", "visibility": "public"} for _ in range(3)]
    )
    surface = {item["module"]: item for item in design_stage6_contracts._module_surface(project, rows)}
    assert surface["wide"]["public_ratio"] == 0.857 and surface["wide"]["shallow"] is True
    assert surface["gateway"]["depth_kind"] == "facade" and surface["gateway"]["shallow"] is False
    assert surface["narrow"]["shallow"] is False  # below the minimum owned-function count


def test_cabinet_state6_surface_has_no_shallow_module() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    assert [item["module"] for item in report["module_surface"] if item["shallow"]] == []


def _add_returner(project: Path, function: str, module: str, signature: str) -> None:
    plan_path = project / PLAN
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["functions"].append({
        "function": function, "module": module, "visibility": "internal",
        "purpose": "hands the port to a caller", "public_operation": None, "router_operation": None,
    })
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    catalog_path = project / CATALOG
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["contracts"][function] = signature
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")


def test_interface_returned_without_a_declared_provider_is_an_error_with_a_prescription(tmp_path: Path) -> None:
    project = _project(tmp_path)
    modules = sorted({e["module"] for e in json.loads((project / PLAN).read_text())["functions"] if e["module"] != "module:models"})
    first, second = modules[0], modules[1]
    _add_returner(project, "WirePort.read_chunk", "module:models", "(self, max_bytes: int) -> bytes")
    _add_returner(project, "hand_out_backend", first, "(self) -> WirePort")
    _add_returner(project, "relay_backend", second, "(self) -> WirePort | None")

    report = design_stage6_contracts.coverage(project)
    findings = [f for f in report["findings"] if f["code"] == "interface_without_provider"]
    assert len(findings) == 1 and findings[0]["severity"] == "error"
    finding = findings[0]
    assert finding["interface"] == "WirePort"
    assert finding["operations"] == ["read_chunk"]
    assert finding["returned_by"] == [f"{first.removeprefix('module:')}.hand_out_backend", f"{second.removeprefix('module:')}.relay_backend"]
    assert finding["modules"] == sorted(m.removeprefix("module:") for m in (first, second))
    assert "Declare the provider in 60_contract_plan.json" in finding["message"]
    plan_entries = finding["prescription"]["plan_entries"]
    assert {e["module"] for e in plan_entries} == {first, second}
    assert [e["function"].split(".", 1)[1] for e in plan_entries if e["module"] == first] == ["__init__", "read_chunk"]
    assert finding["prescription"]["contract_entries"][plan_entries[1]["function"]] == "(self, max_bytes: int) -> bytes"
    assert all(e["visibility"] == "internal" for e in plan_entries)
    assert report["summary"]["handoff_ready"] is False

    # a note that claims the module-owned implementation pins the prescription to that module
    (project / "80_notes.md").write_text(
        "hand_out_backend: [DEPENDENCY_BOUNDARY] MUST construct the module-owned concrete WirePort.\n",
        encoding="utf-8",
    )
    finding = next(f for f in design_stage6_contracts.coverage(project)["findings"] if f["code"] == "interface_without_provider")
    assert finding["modules"] == [first.removeprefix("module:")]
    assert "module-owned" in finding["message"]

    # declaring the provider, method by method, clears the finding
    provider = "OwnedWirePort"
    _add_returner(project, f"{provider}.__init__", first, "(self, payload: bytes) -> None")
    _add_returner(project, f"{provider}.read_chunk", first, "(self, max_bytes: int) -> bytes")
    report = design_stage6_contracts.coverage(project)
    assert [f for f in report["findings"] if f["code"] == "interface_without_provider"] == []


def test_cabinet_state6_interfaces_all_have_providers() -> None:
    report = design_stage6_contracts.coverage(CABINET)
    assert [f for f in report["findings"] if f["code"] == "interface_without_provider"] == []
