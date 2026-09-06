#!/usr/bin/env python3
"""Compile capability execution readiness from a box, provider profile, and binding contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


IMPLEMENTED_CAPABILITY_EXECUTION_RULES = (
    "CAP-EXEC-REL-001",
    "CAP-EXEC-PRE-001",
    "CAP-EXEC-PROJ-001",
    "CAP-EXEC-VERIFY-001",
    "CAP-EXEC-SEM-001",
)


@dataclass(frozen=True)
class ReadinessGap:
    code: str
    subject: str
    message: str


@dataclass(frozen=True)
class ReadinessReport:
    schema_version: str
    capability_id: str
    status: str
    host_verification_gate: str
    capability_readiness_gate: str
    language_rules: tuple[str, ...]
    blocking_gaps: tuple[ReadinessGap, ...]


def _load(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected mapping document: {path}")
    return value


def _git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    header = f"blob {len(payload)}\0".encode()
    return hashlib.sha1(header + payload).hexdigest()


def _status(value: Any) -> str:
    return value if isinstance(value, str) else "UNVERIFIED"


def _provider_statuses_from_mapping(providers: Any) -> dict[str, str]:
    if not isinstance(providers, dict):
        return {}
    result: dict[str, str] = {}
    for provider_id, provider in providers.items():
        if not isinstance(provider, dict):
            result[str(provider_id)] = "UNVERIFIED"
            continue
        verification = provider.get("verification")
        if not isinstance(verification, dict):
            result[str(provider_id)] = "UNVERIFIED"
            continue
        result[str(provider_id)] = _status(verification.get("status"))
    return result


def _provider_statuses(profile: dict[str, Any]) -> dict[str, str]:
    return _provider_statuses_from_mapping(profile.get("providers"))


def _execution_provider_statuses(contract: dict[str, Any]) -> dict[str, str]:
    return _provider_statuses_from_mapping(contract.get("execution_providers"))


def _execution_runtime_dependencies(contract: dict[str, Any]) -> tuple[set[str], set[str]]:
    declared: set[str] = set()
    providers = contract.get("execution_providers")
    if isinstance(providers, dict):
        for provider in providers.values():
            if not isinstance(provider, dict):
                continue
            dependencies = provider.get("runtime_dependencies")
            if isinstance(dependencies, list):
                declared.update(str(item) for item in dependencies)

    projection = contract.get("runtime_projection")
    projected: set[str] = set()
    if isinstance(projection, dict):
        dependencies = projection.get("dependencies")
        if isinstance(dependencies, list):
            projected.update(str(item) for item in dependencies)
    return declared, projected


def _add_contract_drift(
    gaps: list[ReadinessGap],
    subject: str,
    expected: Any,
    observed: Any,
) -> None:
    if expected != observed:
        gaps.append(
            ReadinessGap(
                "CAPABILITY_CONTRACT_DRIFT",
                subject,
                f"execution contract differs from source capability: expected {expected!r}, observed {observed!r}",
            )
        )


def _binding_provider_ids(binding: dict[str, Any]) -> tuple[str, ...]:
    providers = binding.get("providers")
    if isinstance(providers, list):
        return tuple(str(item) for item in providers)

    direct = binding.get("provider")
    if isinstance(direct, str):
        return (direct,)

    provider_ids: list[str] = []
    for key in (
        "policy_provider",
        "output_validation_provider",
        "authority_decision",
        "durable_persistence",
    ):
        value = binding.get(key)
        if isinstance(value, str):
            provider_ids.append(value)
    return tuple(provider_ids)


def _check_provider_references(
    *,
    subject: str,
    binding: dict[str, Any],
    provider_statuses: dict[str, str],
    gaps: list[ReadinessGap],
) -> None:
    for provider_id in _binding_provider_ids(binding):
        if provider_id not in provider_statuses:
            gaps.append(
                ReadinessGap(
                    "PROVIDER_RELATION_MISSING",
                    subject,
                    f"binding references undeclared provider {provider_id}",
                )
            )
            continue
        if provider_statuses[provider_id] != "PASS":
            gaps.append(
                ReadinessGap(
                    "PROVIDER_UNVERIFIED",
                    subject,
                    f"binding provider {provider_id} is {provider_statuses[provider_id]}",
                )
            )


def compile_readiness(
    box: dict[str, Any],
    profile: dict[str, Any],
    contract: dict[str, Any],
    *,
    box_blob_sha: str | None = None,
) -> ReadinessReport:
    capability_id = str(contract.get("capability_id", ""))
    gaps: list[ReadinessGap] = []

    source_manifest = contract.get("source_manifest")
    if not isinstance(source_manifest, dict):
        gaps.append(
            ReadinessGap(
                "SOURCE_MANIFEST_BINDING_MISSING",
                capability_id,
                "execution contract has no source manifest binding",
            )
        )
    elif box_blob_sha is not None and source_manifest.get("blob_sha") != box_blob_sha:
        gaps.append(
            ReadinessGap(
                "MANIFEST_FINGERPRINT_DRIFT",
                str(source_manifest.get("path", "")),
                "source manifest blob no longer matches the reviewed execution contract",
            )
        )

    capabilities = box.get("capabilities")
    capability = capabilities.get(capability_id) if isinstance(capabilities, dict) else None
    if not isinstance(capability, dict):
        gaps.append(
            ReadinessGap(
                "CAPABILITY_RELATION_MISSING",
                capability_id,
                "source box does not declare the bound capability",
            )
        )
        capability = {}

    source_contract = contract.get("source_capability_contract")
    if not isinstance(source_contract, dict):
        gaps.append(
            ReadinessGap(
                "CAPABILITY_CONTRACT_MISSING",
                capability_id,
                "execution contract has no copied capability contract",
            )
        )
        source_contract = {}

    _add_contract_drift(gaps, "input", capability.get("input"), source_contract.get("input"))
    _add_contract_drift(gaps, "output", capability.get("output"), source_contract.get("output"))
    _add_contract_drift(gaps, "effects", capability.get("effects", []), source_contract.get("effects", []))
    _add_contract_drift(gaps, "requires", capability.get("requires", []), source_contract.get("requires", []))
    _add_contract_drift(
        gaps,
        "deterministic_lowering",
        capability.get("deterministic_lowering", []),
        source_contract.get("deterministic_lowering", []),
    )
    disclosure = capability.get("disclosure") if isinstance(capability.get("disclosure"), dict) else {}
    _add_contract_drift(
        gaps,
        "disclosure_allow",
        disclosure.get("allow", []),
        source_contract.get("disclosure_allow", []),
    )
    _add_contract_drift(
        gaps,
        "disclosure_deny",
        disclosure.get("deny", []),
        source_contract.get("disclosure_deny", []),
    )
    audit = capability.get("audit") if isinstance(capability.get("audit"), dict) else {}
    _add_contract_drift(
        gaps,
        "audit_required",
        audit.get("required"),
        source_contract.get("audit_required"),
    )

    host_provider_statuses = _provider_statuses(profile)
    required_host_statuses = tuple(host_provider_statuses.values())
    host_gate = (
        "pass"
        if required_host_statuses and all(status == "PASS" for status in required_host_statuses)
        else "block"
    )
    if host_gate != "pass":
        gaps.append(
            ReadinessGap(
                "HOST_VERIFICATION_BLOCKED",
                capability_id,
                "capability execution requires every selected generic host provider to be PASS",
            )
        )

    execution_provider_statuses = _execution_provider_statuses(contract)
    collisions = sorted(set(host_provider_statuses) & set(execution_provider_statuses))
    for provider_id in collisions:
        gaps.append(
            ReadinessGap(
                "PROVIDER_ID_COLLISION",
                provider_id,
                "capability execution provider id collides with generic host provider id",
            )
        )
    provider_statuses = {**host_provider_statuses, **execution_provider_statuses}

    declared_runtime_dependencies, projected_runtime_dependencies = _execution_runtime_dependencies(contract)
    for dependency in sorted(declared_runtime_dependencies - projected_runtime_dependencies):
        gaps.append(
            ReadinessGap(
                "RUNTIME_DEPENDENCY_NOT_PROJECTED",
                dependency,
                "capability execution provider dependency is not present in runtime projection",
            )
        )

    declared_steps = capability.get("deterministic_lowering", [])
    if not isinstance(declared_steps, list):
        declared_steps = []
    step_bindings = contract.get("step_bindings")
    if not isinstance(step_bindings, dict):
        step_bindings = {}
    declared_step_names = {str(item) for item in declared_steps}
    if set(step_bindings) != declared_step_names:
        missing = sorted(declared_step_names - set(step_bindings))
        extra = sorted(set(step_bindings) - declared_step_names)
        if missing:
            gaps.append(
                ReadinessGap(
                    "STEP_BINDING_MISSING",
                    capability_id,
                    "missing deterministic step bindings: " + ", ".join(missing),
                )
            )
        if extra:
            gaps.append(
                ReadinessGap(
                    "UNDECLARED_STEP_BINDING",
                    capability_id,
                    "bindings exist for undeclared steps: " + ", ".join(extra),
                )
            )

    for step_name in sorted(declared_step_names & set(step_bindings)):
        binding = step_bindings[step_name]
        if not isinstance(binding, dict):
            gaps.append(ReadinessGap("STEP_BINDING_INVALID", step_name, "step binding must be a mapping"))
            continue
        if binding.get("status") != "RESOLVED":
            gaps.append(
                ReadinessGap(
                    "LOWERING_GAP",
                    step_name,
                    str(binding.get("reason", "deterministic step binding is unresolved")),
                )
            )
            continue
        _check_provider_references(
            subject=step_name,
            binding=binding,
            provider_statuses=provider_statuses,
            gaps=gaps,
        )

    declared_requires = capability.get("requires", [])
    if not isinstance(declared_requires, list):
        declared_requires = []
    precondition_bindings = contract.get("precondition_bindings")
    if not isinstance(precondition_bindings, dict):
        precondition_bindings = {}
    declared_require_names = {str(item) for item in declared_requires}
    if set(precondition_bindings) != declared_require_names:
        missing = sorted(declared_require_names - set(precondition_bindings))
        extra = sorted(set(precondition_bindings) - declared_require_names)
        if missing:
            gaps.append(
                ReadinessGap(
                    "PRECONDITION_BINDING_MISSING",
                    capability_id,
                    "missing required precondition bindings: " + ", ".join(missing),
                )
            )
        if extra:
            gaps.append(
                ReadinessGap(
                    "UNDECLARED_PRECONDITION_BINDING",
                    capability_id,
                    "bindings exist for undeclared preconditions: " + ", ".join(extra),
                )
            )

    for requirement in sorted(declared_require_names & set(precondition_bindings)):
        binding = precondition_bindings[requirement]
        if not isinstance(binding, dict):
            gaps.append(
                ReadinessGap(
                    "PRECONDITION_BINDING_INVALID",
                    requirement,
                    "precondition binding must be a mapping",
                )
            )
            continue
        if binding.get("status") != "RESOLVED":
            gaps.append(
                ReadinessGap(
                    str(binding.get("gap_class", "LOWERING_GAP")),
                    requirement,
                    str(binding.get("reason", "required precondition binding is unresolved")),
                )
            )
            continue
        _check_provider_references(
            subject=requirement,
            binding=binding,
            provider_statuses=provider_statuses,
            gaps=gaps,
        )

    for binding_name in ("audit_binding", "disclosure_binding"):
        binding = contract.get(binding_name)
        if not isinstance(binding, dict):
            gaps.append(
                ReadinessGap(
                    "REQUIRED_BINDING_MISSING",
                    binding_name,
                    f"{binding_name} is required before protected execution",
                )
            )
            continue
        if binding.get("status") != "RESOLVED":
            gaps.append(
                ReadinessGap("LOWERING_GAP", binding_name, f"{binding_name} is unresolved")
            )
            continue
        _check_provider_references(
            subject=binding_name,
            binding=binding,
            provider_statuses=provider_statuses,
            gaps=gaps,
        )

    readiness_gate = "pass" if not gaps else "block"
    status = "ready" if readiness_gate == "pass" else "blocked"
    return ReadinessReport(
        schema_version="spec_workbench_capability_execution_readiness.v0",
        capability_id=capability_id,
        status=status,
        host_verification_gate=host_gate,
        capability_readiness_gate=readiness_gate,
        language_rules=IMPLEMENTED_CAPABILITY_EXECUTION_RULES,
        blocking_gaps=tuple(gaps),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("box", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("contract", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    box = _load(args.box)
    profile = _load(args.profile)
    contract = _load(args.contract)
    report = compile_readiness(
        box,
        profile,
        contract,
        box_blob_sha=_git_blob_sha(args.box),
    )
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print(f"Capability execution readiness: {report.capability_readiness_gate}")
        print(f"Capability: {report.capability_id}")
        print(f"Host verification: {report.host_verification_gate}")
        for gap in report.blocking_gaps:
            print(f"- {gap.code} {gap.subject}: {gap.message}")
    return 0 if report.capability_readiness_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
