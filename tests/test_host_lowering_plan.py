from __future__ import annotations

import hashlib
from copy import deepcopy
from pathlib import Path

import yaml

from host_lowering_plan import IMPLEMENTED_HOST_LOWERING_RULES, compile_host_lowering


ROOT = Path(__file__).resolve().parents[1]
BOX_PATH = ROOT / "experiments" / "cabinet-vault" / "cabinet_backend_box_v0.yaml"
PROFILE_PATH = ROOT / "experiments" / "cabinet-vault" / "generic_host_profile_candidate_v0.yaml"
CONTRACT_PATH = ROOT / "experiments" / "cabinet-vault" / "generic_host_lowering_contract_v0.yaml"
TOOL_PATH = ROOT / "tools" / "host_lowering_plan.py"


def load(path: Path):
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def definitions():
    return load(BOX_PATH), load(PROFILE_PATH)


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def test_candidate_archive_host_plan_resolves_relations_and_dependency_projection():
    box, profile = definitions()
    plan = compile_host_lowering(box, profile)

    assert plan.status == "compiled"
    assert plan.verification_gate == "block"
    assert plan.gaps == ()
    assert set(plan.runtime_dependencies) == {"pydantic", "psycopg"}
    assert {item.requirement for item in plan.relations} == set(box["host_requirements"])
    assert {item.provider_id for item in plan.provider_verification} == set(profile["providers"])

    verification = {item.provider_id: item.verification_status for item in plan.provider_verification}
    assert {
        provider_id
        for provider_id, status in verification.items()
        if status == "PASS"
    } == {
        "postgres_record_kernel",
        "local_private_byte_vault",
    }
    assert {
        provider_id
        for provider_id, status in verification.items()
        if status == "UNVERIFIED"
    } == {
        "authority_kernel",
        "typed_schema_kernel",
        "protected_configuration_kernel",
    }


def test_missing_required_interface_relation_blocks_lowering():
    box, profile = definitions()
    broken = deepcopy(profile)
    broken["providers"]["postgres_record_kernel"]["satisfies"].remove("resource_locking")

    plan = compile_host_lowering(box, broken)

    assert plan.status == "unresolved"
    assert plan.verification_gate == "block"
    assert any(
        gap.code == "IMPLEMENTATION_RELATION_MISSING" and gap.subject == "resource_locking"
        for gap in plan.gaps
    )


def test_ambiguous_required_interface_relation_blocks_lowering():
    box, profile = definitions()
    broken = deepcopy(profile)
    broken["providers"]["second_record_kernel"] = {
        "satisfies": ["resource_locking"],
        "runtime_dependencies": [],
        "verification": {"required": True, "status": "UNVERIFIED"},
    }

    plan = compile_host_lowering(box, broken)

    assert plan.status == "unresolved"
    gap = next(gap for gap in plan.gaps if gap.code == "AMBIGUOUS_IMPLEMENTATION_RELATION")
    assert gap.subject == "resource_locking"
    assert set(gap.candidates) == {"postgres_record_kernel", "second_record_kernel"}


def test_lost_psycopg_projection_blocks_lowering_before_execution():
    box, profile = definitions()
    broken = deepcopy(profile)
    broken["runtime_projection"]["dependencies"].remove("psycopg")

    plan = compile_host_lowering(box, broken)

    assert plan.status == "unresolved"
    assert plan.verification_gate == "block"
    assert any(
        gap.code == "RUNTIME_DEPENDENCY_NOT_PROJECTED" and gap.subject == "psycopg"
        for gap in plan.gaps
    )


def test_required_skip_normalizes_to_unverified():
    box, profile = definitions()
    changed = deepcopy(profile)
    changed["providers"]["authority_kernel"]["verification"]["status"] = "SKIP"

    plan = compile_host_lowering(box, changed)
    authority = next(
        item for item in plan.provider_verification if item.provider_id == "authority_kernel"
    )

    assert authority.declared_status == "SKIP"
    assert authority.verification_status == "UNVERIFIED"
    assert plan.verification_gate == "block"


def test_verification_gate_passes_only_when_every_required_provider_passes():
    box, profile = definitions()
    verified = deepcopy(profile)
    for provider in verified["providers"].values():
        provider["verification"]["status"] = "PASS"

    plan = compile_host_lowering(box, verified)

    assert plan.status == "compiled"
    assert plan.verification_gate == "pass"
    assert {item.verification_status for item in plan.provider_verification} == {"PASS"}


def test_planner_declares_exact_contract_rules_and_reviewed_source_fingerprint():
    contract = load(CONTRACT_PATH)
    binding = contract["tool_bindings"]["host_lowering_plan"]

    assert set(binding["declared_rules"]) == set(IMPLEMENTED_HOST_LOWERING_RULES)
    assert binding["implementation"] == "tools/host_lowering_plan.py"
    assert binding["implementation_blob_sha"] == git_blob_sha(TOOL_PATH)


def test_candidate_profile_contains_no_product_specific_dependencies():
    _, profile = definitions()

    assert profile["product_specific_dependencies"] == []
