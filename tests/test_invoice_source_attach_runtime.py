from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from invoice_source_attach_models import models
from invoice_source_attach_runtime_probe import run_probe
from typed_schema_kernel import TypedSchemaKernel


ROOT = Path(__file__).resolve().parents[1]
LOWERING = ROOT / "experiments" / "cabinet-vault" / "invoice_source_attach_runtime_lowering_v0.yaml"
EXECUTION_CONTRACT = ROOT / "experiments" / "cabinet-vault" / "invoice_source_attach_execution_contract_v0.yaml"
MODELS = ROOT / "tools" / "invoice_source_attach_models.py"
RUNTIME = ROOT / "tools" / "invoice_source_attach_runtime.py"
PROBE = ROOT / "tools" / "invoice_source_attach_runtime_probe.py"


def load(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def test_runtime_lowering_is_bound_to_ready_execution_contract_and_exact_implementation_blobs():
    lowering = load(LOWERING)
    contract = load(EXECUTION_CONTRACT)

    assert contract["expected_readiness"] == {
        "host_verification_gate": "pass",
        "capability_readiness_gate": "pass",
        "blocking_gaps": [],
    }
    assert lowering["source_execution_contract"]["blob_sha"] == git_blob_sha(EXECUTION_CONTRACT)
    bindings = lowering["implementation_bindings"]
    assert bindings["typed_models"]["blob_sha"] == git_blob_sha(MODELS)
    assert bindings["executor"]["blob_sha"] == git_blob_sha(RUNTIME)
    assert bindings["probe_runner"]["blob_sha"] == git_blob_sha(PROBE)
    assert bindings["probe_runner"]["successful_exit"] == 0
    assert bindings["probe_runner"]["blocking_exit"] == 2


def test_runtime_rules_have_exact_probe_obligations_and_remain_unverified_before_execution():
    lowering = load(LOWERING)

    assert set(lowering["runtime_rules"]) == {
        f"ATTACH-RUNTIME-{index:03d}" for index in range(1, 10)
    }
    assert lowering["verification"]["status"] == "UNVERIFIED"
    assert lowering["verification"]["probes"] == [
        f"ATTACH-PROBE-{index:03d}" for index in range(1, 8)
    ]
    assert len(lowering["verification_obligations"]) == 7


def test_first_execution_case_is_explicitly_single_file_and_cannot_invent_source_identity():
    lowering = load(LOWERING)

    assert lowering["execution_case"] == "attach_expected_missing_source"
    assert lowering["execution_case_constraints"]["file_count"] == "exactly_one"
    assert "invent_source_id" in lowering["forbidden_runtime_behavior"]
    assert "use_invoice_number_as_mutation_key" in lowering["forbidden_runtime_behavior"]
    assert "mutate_immutable_invoice_card" in lowering["forbidden_runtime_behavior"]


def test_runtime_composition_does_not_reintroduce_classical_service_repository_router_ownership():
    text = RUNTIME.read_text(encoding="utf-8")
    forbidden = (
        "DurableArchiveService",
        "ArchiveUnitOfWork",
        "PostgresArchiveUnitOfWork",
        "SourceByteStore",
        "FastAPI",
        "APIRouter",
        "Repository",
    )
    assert all(item not in text for item in forbidden)


def test_nested_runtime_models_validate_without_forward_ref_resolution_errors():
    InputModel, OutputModel = models()
    kernel = TypedSchemaKernel()

    validated = kernel.validate_input(
        InputModel,
        {
            "invoice_id": "invoice-1",
            "files": (
                {
                    "filename": "source.png",
                    "media_type": "image/png",
                    "content": b"bytes",
                    "expected_source_id": "source-1",
                    "expected_content_hash": "a" * 64,
                },
            ),
            "expected_sources": (
                {
                    "content_kind": "source",
                    "content_id": "source-1",
                    "content_hash": "a" * 64,
                    "size_bytes": 5,
                    "media_type": "image/png",
                },
            ),
        },
    )
    assert validated.invoice_id == "invoice-1"
    assert validated.files[0].expected_source_id == "source-1"

    output = kernel.validate_output(
        OutputModel,
        {
            "invoice_id": "invoice-1",
            "items": (
                {
                    "filename": "source.png",
                    "source_id": "source-1",
                    "content_hash": "a" * 64,
                    "result": "attached",
                    "safe_error_code": None,
                },
            ),
            "source_status": {
                "invoice_id": "invoice-1",
                "available_source_ids": ("source-1",),
                "missing_source_ids": (),
                "failed_source_ids": (),
                "completeness": "complete",
                "active_loss_decision_ids": (),
                "complete": True,
                "observed_at": datetime.now(timezone.utc),
            },
        },
    )
    assert output.source_status.complete is True


def test_runtime_probe_without_protected_configuration_fails_closed_as_unverified():
    report = run_probe({})

    assert report.status == "block"
    assert len(report.results) == 7
    assert [item.probe_id for item in report.results] == [
        f"ATTACH-PROBE-{index:03d}" for index in range(1, 8)
    ]
    assert {item.status for item in report.results} == {"UNVERIFIED"}
