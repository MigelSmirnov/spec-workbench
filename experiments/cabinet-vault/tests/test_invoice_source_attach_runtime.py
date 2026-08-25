from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import yaml

from invoice_source_attach_models import models
from invoice_source_attach_runtime_probe import run_probe
from typed_schema_kernel import TypedSchemaKernel


ROOT = Path(__file__).resolve().parents[3]
LOWERING = ROOT / "experiments" / "cabinet-vault" / "invoice_source_attach_runtime_lowering_v0.yaml"
EXECUTION_CONTRACT = ROOT / "experiments" / "cabinet-vault" / "invoice_source_attach_execution_contract_v0.yaml"
EVIDENCE = ROOT / "experiments" / "cabinet-vault" / "INVOICE_SOURCE_ATTACH_RUNTIME_EVIDENCE.md"
MODELS = ROOT / "experiments" / "cabinet-vault" / "tools" / "invoice_source_attach_models.py"
RUNTIME = ROOT / "experiments" / "cabinet-vault" / "tools" / "invoice_source_attach_runtime.py"
PROBE = ROOT / "experiments" / "cabinet-vault" / "tools" / "invoice_source_attach_runtime_probe.py"


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


def test_runtime_rules_and_probe_obligations_are_evidence_backed_pass():
    lowering = load(LOWERING)

    assert set(lowering["runtime_rules"]) == {
        f"ATTACH-RUNTIME-{index:03d}" for index in range(1, 10)
    }
    verification = lowering["verification"]
    assert lowering["status"] == "verified_execution_case"
    assert verification["status"] == "PASS"
    assert verification["runtime_evidence"] == {
        "record": "experiments/cabinet-vault/INVOICE_SOURCE_ATTACH_RUNTIME_EVIDENCE.md",
        "executed_on": "2026-08-21",
        "result": "PASS",
        "exit_code": 0,
    }
    assert EVIDENCE.is_file()
    probes = verification["probes"]
    assert [item["id"] for item in probes] == [
        f"ATTACH-PROBE-{index:03d}" for index in range(1, 8)
    ]
    assert {item["status"] for item in probes} == {"PASS"}
    assert {item["executed"] for item in probes} == {True}
    assert all(item["proves"] for item in probes)
    assert len(lowering["verification_obligations"]) == 7


def test_verified_scope_is_explicitly_narrower_than_full_capability_surface():
    lowering = load(LOWERING)
    scope = lowering["verified_scope"]

    assert lowering["execution_case"] == "attach_expected_missing_source"
    assert lowering["execution_case_constraints"]["file_count"] == "exactly_one"
    assert "single_file_expected_missing_source_attachment" in scope["proves"]
    assert "explicit_invoice_id_target" in scope["proves"]
    assert "existing_expected_source_id_only" in scope["proves"]
    assert {
        "multi_file_batch_orchestration",
        "source_identity_generation",
        "invoice_number_search_or_disambiguation",
        "attachment_to_nonaccepted_invoice",
        "transport_exposure",
    }.issubset(set(scope["does_not_prove"]))
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


def test_runtime_probe_without_protected_configuration_still_fails_closed_as_unverified():
    report = run_probe({})

    assert report.status == "block"
    assert len(report.results) == 7
    assert [item.probe_id for item in report.results] == [
        f"ATTACH-PROBE-{index:03d}" for index in range(1, 8)
    ]
    assert {item.status for item in report.results} == {"UNVERIFIED"}
