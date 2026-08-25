#!/usr/bin/env python3
"""Compile declared box host requirements into a fail-closed generic lowering plan."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


PLAN_SCHEMA_VERSION = "spec_workbench_host_lowering_plan.v0"
SUPPORTED_PROFILE_VERSION = "cabinet_generic_host_profile.v0"
VALID_VERIFICATION_STATUSES = frozenset({"PASS", "FAIL", "UNVERIFIED", "SKIP"})

IMPLEMENTED_HOST_LOWERING_RULES = frozenset(
    {
        "GHL-REL-001",
        "GHL-PROJ-001",
        "GHL-VERIFY-001",
        "GHL-VERIFY-002",
    }
)


@dataclass(frozen=True)
class LoweringGap:
    code: str
    subject: str
    message: str
    candidates: tuple[str, ...] = ()


@dataclass(frozen=True)
class ProviderRelation:
    requirement: str
    provider_id: str


@dataclass(frozen=True)
class ProviderVerification:
    provider_id: str
    required: bool
    declared_status: str | None
    verification_status: str


@dataclass(frozen=True)
class HostLoweringPlan:
    schema_version: str
    box_id: str | None
    profile_id: str | None
    status: str
    verification_gate: str
    relations: tuple[ProviderRelation, ...]
    runtime_dependencies: tuple[str, ...]
    provider_verification: tuple[ProviderVerification, ...]
    gaps: tuple[LoweringGap, ...]
    language_rules: tuple[str, ...]


def load_definition(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyYAML is required to load host lowering definitions") from exc

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"{path} must contain a mapping")
    return value


def _effective_verification(required: bool, declared: str | None) -> str:
    if required and declared in {None, "SKIP", "UNVERIFIED"}:
        return "UNVERIFIED"
    if declared is None:
        return "SKIP"
    return declared


def compile_host_lowering(
    box: dict[str, Any],
    profile: dict[str, Any],
) -> HostLoweringPlan:
    gaps: list[LoweringGap] = []
    relations: list[ProviderRelation] = []

    box_meta = box.get("cabinet")
    box_id = box_meta.get("id") if isinstance(box_meta, dict) else None
    if not isinstance(box_id, str) or not box_id:
        box_id = None
        gaps.append(LoweringGap("INVALID_BOX_ID", "cabinet.id", "box must declare a non-empty id"))

    profile_version = profile.get("profile_version")
    if profile_version != SUPPORTED_PROFILE_VERSION:
        gaps.append(
            LoweringGap(
                "UNSUPPORTED_PROFILE_VERSION",
                str(profile_version),
                f"expected {SUPPORTED_PROFILE_VERSION}",
            )
        )

    profile_id = profile.get("profile_id")
    if not isinstance(profile_id, str) or not profile_id:
        profile_id = None
        gaps.append(LoweringGap("INVALID_PROFILE_ID", "profile_id", "profile must declare a non-empty id"))

    requirements = box.get("host_requirements")
    if (
        not isinstance(requirements, list)
        or not requirements
        or not all(isinstance(item, str) and item for item in requirements)
    ):
        gaps.append(
            LoweringGap(
                "INVALID_HOST_REQUIREMENTS",
                "host_requirements",
                "box host_requirements must be a non-empty list of strings",
            )
        )
        requirements = []

    providers = profile.get("providers")
    if not isinstance(providers, dict):
        gaps.append(LoweringGap("INVALID_PROVIDERS", "providers", "profile providers must be a mapping"))
        providers = {}

    normalized_providers: dict[str, dict[str, Any]] = {}
    for provider_id, provider in sorted(providers.items()):
        if not isinstance(provider_id, str) or not provider_id or not isinstance(provider, dict):
            gaps.append(
                LoweringGap(
                    "INVALID_PROVIDER",
                    str(provider_id),
                    "provider id must be non-empty and provider definition must be a mapping",
                )
            )
            continue

        satisfies = provider.get("satisfies")
        dependencies = provider.get("runtime_dependencies")
        if (
            not isinstance(satisfies, list)
            or not satisfies
            or not all(isinstance(item, str) and item for item in satisfies)
        ):
            gaps.append(
                LoweringGap(
                    "INVALID_PROVIDER_RELATIONS",
                    provider_id,
                    "provider satisfies must be a non-empty list of host requirement ids",
                )
            )
            continue
        if (
            not isinstance(dependencies, list)
            or not all(isinstance(item, str) and item for item in dependencies)
        ):
            gaps.append(
                LoweringGap(
                    "INVALID_RUNTIME_DEPENDENCIES",
                    provider_id,
                    "runtime_dependencies must be a list of dependency ids",
                )
            )
            continue

        normalized_providers[provider_id] = provider

    selected_provider_ids: set[str] = set()
    for requirement in sorted(set(requirements)):
        candidates = tuple(
            provider_id
            for provider_id, provider in normalized_providers.items()
            if requirement in provider["satisfies"]
        )
        if not candidates:
            gaps.append(
                LoweringGap(
                    "IMPLEMENTATION_RELATION_MISSING",
                    requirement,
                    "required host interface has no selected implementation relation",
                )
            )
            continue
        if len(candidates) != 1:
            gaps.append(
                LoweringGap(
                    "AMBIGUOUS_IMPLEMENTATION_RELATION",
                    requirement,
                    "required host interface must resolve to exactly one selected implementation",
                    candidates=tuple(sorted(candidates)),
                )
            )
            continue

        provider_id = candidates[0]
        selected_provider_ids.add(provider_id)
        relations.append(ProviderRelation(requirement=requirement, provider_id=provider_id))

    required_dependencies = {
        dependency
        for provider_id in selected_provider_ids
        for dependency in normalized_providers[provider_id]["runtime_dependencies"]
    }

    projection = profile.get("runtime_projection")
    projected_dependencies: set[str] = set()
    if not isinstance(projection, dict):
        gaps.append(
            LoweringGap(
                "INVALID_RUNTIME_PROJECTION",
                "runtime_projection",
                "profile must declare runtime_projection mapping",
            )
        )
    else:
        dependencies = projection.get("dependencies")
        if (
            not isinstance(dependencies, list)
            or not all(isinstance(item, str) and item for item in dependencies)
        ):
            gaps.append(
                LoweringGap(
                    "INVALID_RUNTIME_PROJECTION",
                    "runtime_projection.dependencies",
                    "projected dependencies must be a list of dependency ids",
                )
            )
        else:
            projected_dependencies = set(dependencies)

    for dependency in sorted(required_dependencies - projected_dependencies):
        gaps.append(
            LoweringGap(
                "RUNTIME_DEPENDENCY_NOT_PROJECTED",
                dependency,
                "selected lowering dependency is absent from runtime projection",
            )
        )

    provider_verification: list[ProviderVerification] = []
    for provider_id in sorted(selected_provider_ids):
        provider = normalized_providers[provider_id]
        verification = provider.get("verification")
        required = True
        declared_status: str | None = None

        if verification is not None and not isinstance(verification, dict):
            gaps.append(
                LoweringGap(
                    "INVALID_PROVIDER_VERIFICATION",
                    provider_id,
                    "verification must be a mapping when present",
                )
            )
        elif isinstance(verification, dict):
            required_value = verification.get("required", True)
            if not isinstance(required_value, bool):
                gaps.append(
                    LoweringGap(
                        "INVALID_PROVIDER_VERIFICATION_REQUIRED",
                        provider_id,
                        "verification.required must be boolean",
                    )
                )
            else:
                required = required_value

            status_value = verification.get("status")
            if status_value is not None:
                if not isinstance(status_value, str) or status_value not in VALID_VERIFICATION_STATUSES:
                    gaps.append(
                        LoweringGap(
                            "INVALID_PROVIDER_VERIFICATION_STATUS",
                            provider_id,
                            "verification.status must be PASS, FAIL, UNVERIFIED, or SKIP",
                        )
                    )
                else:
                    declared_status = status_value

        provider_verification.append(
            ProviderVerification(
                provider_id=provider_id,
                required=required,
                declared_status=declared_status,
                verification_status=_effective_verification(required, declared_status),
            )
        )

    structural_status = "compiled" if not gaps else "unresolved"
    verification_gate = "block"
    if not gaps and all(
        (not item.required) or item.verification_status == "PASS"
        for item in provider_verification
    ):
        verification_gate = "pass"

    return HostLoweringPlan(
        schema_version=PLAN_SCHEMA_VERSION,
        box_id=box_id,
        profile_id=profile_id,
        status=structural_status,
        verification_gate=verification_gate,
        relations=tuple(sorted(relations, key=lambda item: item.requirement)),
        runtime_dependencies=tuple(sorted(required_dependencies)),
        provider_verification=tuple(provider_verification),
        gaps=tuple(gaps),
        language_rules=tuple(sorted(IMPLEMENTED_HOST_LOWERING_RULES)),
    )


def render_json(plan: HostLoweringPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


def render_human(plan: HostLoweringPlan) -> str:
    lines = [
        f"Host lowering plan: {plan.status}",
        f"Box: {plan.box_id}",
        f"Profile: {plan.profile_id}",
        f"Verification gate: {plan.verification_gate}",
    ]
    for relation in plan.relations:
        lines.append(f"- {relation.requirement} -> {relation.provider_id}")
    if plan.runtime_dependencies:
        lines.append(f"Runtime dependencies: {', '.join(plan.runtime_dependencies)}")
    for verification in plan.provider_verification:
        lines.append(
            f"- verification {verification.provider_id}: {verification.verification_status}"
        )
    for gap in plan.gaps:
        suffix = f" candidates={','.join(gap.candidates)}" if gap.candidates else ""
        lines.append(f"- {gap.code}: {gap.subject} — {gap.message}{suffix}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("box", type=Path)
    parser.add_argument("profile", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    plan = compile_host_lowering(load_definition(args.box), load_definition(args.profile))
    print(render_json(plan) if args.as_json else render_human(plan), end="")
    return 0 if plan.status == "compiled" and plan.verification_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
