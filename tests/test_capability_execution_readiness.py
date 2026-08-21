from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

import yaml

from capability_execution_readiness import (
    IMPLEMENTED_CAPABILITY_EXECUTION_RULES,
    compile_readiness,
)


ROOT = Path(__file__).resolve().parents[1]
BOX_PATH = ROOT / "experiments" / "cabinet-vault" / "cabinet_backend_box_v0.yaml"
PROFILE_PATH = ROOT / "experiments" / "cabinet-vault" / "generic_host_profile_candidate_v0.yaml"
CONTRACT_PATH = ROOT / "experiments" / "cabinet-vault" / "invoice_source_attach_execution_contract_v0.yaml"
TOOL_PATH = ROOT / "tools" / "capability_execution_readiness.py"
CONTENT_PROVIDER_PATH = ROOT / "tools" / "bounded_content_validation_kernel.py"
CONTENT_PROBE_PATH = ROOT / "tools" / "bounded_content_validation_kernel_probe.py"


def load(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def definitions():
    return load(BOX_PATH), load(PROFILE_PATH), load(CONTRACT_PATH)


def test_verified_host_and_execution_provider_make_capability_ready():
    box, profile, contract = definitions()
    report = compile_readiness(
        box,
        profile,
        contract,
        box_blob_sha=git_blob_sha(BOX_PATH),
    )

    assert report.status == "ready"
    assert report.host_verification_gate == "pass"
    assert report.capability_readiness_gate == "pass"
    assert report.blocking_gaps == ()


def test_contract_copies_the_exact_declared_capability_surface_and_steps():
    box, _, contract = definitions()
    capability = box["capabilities"]["invoice.source.attach"]
    copied = contract["source_capability_contract"]

    assert copied["input"] == capability["input"]
    assert copied["output"] == capability["output"]
    assert copied["effects"] == capability["effects"]
    assert copied["requires"] == capability["requires"]
    assert copied["deterministic_lowering"] == capability["deterministic_lowering"]
    assert copied["disclosure_allow"] == capability["disclosure"]["allow"]
    assert copied["disclosure_deny"] == capability["disclosure"]["deny"]
    assert copied["audit_required"] is capability["audit"]["required"]
    assert set(contract["step_bindings"]) == set(capability["deterministic_lowering"])
    assert set(contract["precondition_bindings"]) == set(capability["requires"])


def test_source_readiness_and_content_provider_fingerprints_are_bound():
    _, _, contract = definitions()
    source = contract["source_manifest"]
    tool = contract["tool_bindings"]["capability_execution_readiness"]
    provider = contract["execution_providers"]["bounded_content_validation_kernel"]

    assert source["path"] == "experiments/cabinet-vault/cabinet_backend_box_v0.yaml"
    assert source["blob_sha"] == git_blob_sha(BOX_PATH)
    assert tool["implementation"] == "tools/capability_execution_readiness.py"
    assert tool["implementation_blob_sha"] == git_blob_sha(TOOL_PATH)
    assert set(tool["declared_rules"]) == set(IMPLEMENTED_CAPABILITY_EXECUTION_RULES)
    assert set(contract["machine_rules"]) == set(IMPLEMENTED_CAPABILITY_EXECUTION_RULES)
    assert provider["implementation"]["blob_sha"] == git_blob_sha(CONTENT_PROVIDER_PATH)
    assert provider["probe_runner"]["blob_sha"] == git_blob_sha(CONTENT_PROBE_PATH)
    assert provider["verification"]["status"] == "PASS"
    evidence = provider["verification"]["evidence"]
    assert evidence == [
        "experiments/cabinet-vault/BOUNDED_CONTENT_VALIDATION_RUNTIME_EVIDENCE.md"
    ]
    assert all((ROOT / item).is_file() for item in evidence)


def test_manifest_fingerprint_drift_blocks_execution_readiness():
    box, profile, contract = definitions()
    report = compile_readiness(
        box,
        profile,
        contract,
        box_blob_sha="0" * 40,
    )

    assert report.capability_readiness_gate == "block"
    assert any(gap.code == "MANIFEST_FINGERPRINT_DRIFT" for gap in report.blocking_gaps)


def test_missing_deterministic_step_binding_blocks_execution():
    box, profile, contract = definitions()
    broken = deepcopy(contract)
    del broken["step_bindings"]["lock_invoice"]

    report = compile_readiness(
        box,
        profile,
        broken,
        box_blob_sha=git_blob_sha(BOX_PATH),
    )

    assert report.capability_readiness_gate == "block"
    assert any(gap.code == "STEP_BINDING_MISSING" for gap in report.blocking_gaps)


def test_provider_regression_blocks_capability_even_when_binding_is_resolved():
    box, profile, contract = definitions()
    regressed = deepcopy(profile)
    regressed["providers"]["authority_kernel"]["verification"]["status"] = "UNVERIFIED"

    report = compile_readiness(
        box,
        regressed,
        contract,
        box_blob_sha=git_blob_sha(BOX_PATH),
    )

    assert report.host_verification_gate == "block"
    assert report.capability_readiness_gate == "block"
    assert any(gap.code == "HOST_VERIFICATION_BLOCKED" for gap in report.blocking_gaps)
    assert any(
        gap.code == "PROVIDER_UNVERIFIED" and gap.subject == "authenticated_principal"
        for gap in report.blocking_gaps
    )


def test_execution_provider_dependency_projection_is_fail_closed():
    box, profile, contract = definitions()
    broken = deepcopy(contract)
    broken["runtime_projection"]["dependencies"].remove("pypdf")

    report = compile_readiness(
        box,
        profile,
        broken,
        box_blob_sha=git_blob_sha(BOX_PATH),
    )

    assert report.host_verification_gate == "pass"
    assert report.capability_readiness_gate == "block"
    assert any(
        gap.code == "RUNTIME_DEPENDENCY_NOT_PROJECTED" and gap.subject == "pypdf"
        for gap in report.blocking_gaps
    )


def test_execution_provider_verification_regression_blocks_readiness():
    box, profile, contract = definitions()
    unverified = deepcopy(contract)
    unverified["execution_providers"]["bounded_content_validation_kernel"]["verification"][
        "status"
    ] = "UNVERIFIED"

    report = compile_readiness(
        box,
        profile,
        unverified,
        box_blob_sha=git_blob_sha(BOX_PATH),
    )

    assert report.host_verification_gate == "pass"
    assert report.capability_readiness_gate == "block"
    assert [(gap.code, gap.subject) for gap in report.blocking_gaps] == [
        ("PROVIDER_UNVERIFIED", "verified_content_signature")
    ]


def test_semantic_guard_is_explicitly_bound_without_signature_shortcuts():
    _, _, contract = definitions()
    semantic_rule = contract["machine_rules"]["CAP-EXEC-SEM-001"]
    signature_binding = contract["precondition_bindings"]["verified_content_signature"]
    provider = contract["execution_providers"]["bounded_content_validation_kernel"]

    assert semantic_rule["binds_generic_rule"] == "GHL-SEM-001"
    assert signature_binding["status"] == "RESOLVED"
    assert signature_binding["providers"] == ["bounded_content_validation_kernel"]
    assert "magic_prefix_only_as_complete_document_validation" in signature_binding[
        "forbidden_fallbacks"
    ]
    assert provider["verification"]["status"] == "PASS"
    assert set(provider["runtime_dependencies"]) == {"Pillow", "pypdf"}
