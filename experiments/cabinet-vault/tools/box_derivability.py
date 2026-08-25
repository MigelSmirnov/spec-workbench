#!/usr/bin/env python3
"""Prove or reject deterministic field mappings between self-described box capabilities."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


REPORT_SCHEMA_VERSION = "spec_workbench_box_derivability.v0"
IMPLEMENTED_BOX_LANGUAGE_RULES = frozenset(
    {
        "BXL-DERIVE-001",
        "BXL-DERIVE-002",
        "BXL-DERIVE-003",
        "BXL-DERIVE-004",
        "BXL-DERIVE-005",
        "BXL-DERIVE-006",
        "BXL-DERIVE-007",
        "BXL-DERIVE-008",
        "BXL-DERIVE-009",
        "BXL-DERIVE-010",
    }
)


class BoxDerivabilityError(RuntimeError):
    """The derivability request itself is malformed or unsupported."""


@dataclass(frozen=True)
class FieldSpec:
    name: str
    type: str | None
    semantic: str | None
    authority: str | None
    mapping: str


@dataclass(frozen=True)
class MappingStep:
    source_path: str
    target_path: str
    semantic: str
    type: str
    authority: str | None
    operator: str = "exact_project"


@dataclass(frozen=True)
class DerivationGap:
    code: str
    target_path: str
    semantic: str | None
    required_type: str | None
    required_authority: str | None
    candidates: tuple[str, ...]
    message: str


@dataclass(frozen=True)
class DerivationReport:
    schema_version: str
    status: str
    source_capability: str
    source_schema: str
    target_capability: str
    target_schema: str
    mapping: tuple[MappingStep, ...]
    gaps: tuple[DerivationGap, ...]
    language_rules: tuple[str, ...]


def load_definition(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise BoxDerivabilityError("PyYAML is required to load box manifests") from exc

    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BoxDerivabilityError(f"could not read manifest {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BoxDerivabilityError(f"manifest must be a mapping: {path}")
    return value


def _capability_schema(
    definition: dict[str, Any],
    capability_name: str,
    direction: str,
) -> tuple[str, dict[str, Any]]:
    capabilities = definition.get("capabilities")
    schemas = definition.get("schemas")
    if not isinstance(capabilities, dict) or not isinstance(schemas, dict):
        raise BoxDerivabilityError("manifest must define capabilities and schemas mappings")
    capability = capabilities.get(capability_name)
    if not isinstance(capability, dict):
        raise BoxDerivabilityError(f"unknown capability: {capability_name}")
    schema_name = capability.get(direction)
    if not isinstance(schema_name, str) or not schema_name:
        raise BoxDerivabilityError(
            f"capability {capability_name!r} must declare a named {direction} schema"
        )
    schema = schemas.get(schema_name)
    if not isinstance(schema, dict):
        raise BoxDerivabilityError(
            f"capability {capability_name!r} references unknown schema {schema_name!r}"
        )
    fields = schema.get("fields")
    if not isinstance(fields, dict):
        raise BoxDerivabilityError(f"schema {schema_name!r} must declare fields")
    return schema_name, schema


def _field_spec(name: str, value: Any) -> FieldSpec:
    if isinstance(value, str):
        return FieldSpec(name=name, type=value, semantic=None, authority=None, mapping="exact")
    if not isinstance(value, dict):
        return FieldSpec(name=name, type=None, semantic=None, authority=None, mapping="exact")
    field_type = value.get("type")
    semantic = value.get("semantic")
    authority = value.get("authority")
    mapping = value.get("mapping", "exact")
    return FieldSpec(
        name=name,
        type=field_type if isinstance(field_type, str) else None,
        semantic=semantic if isinstance(semantic, str) else None,
        authority=authority if isinstance(authority, str) else None,
        mapping=mapping if isinstance(mapping, str) else "unsupported",
    )


def _fields(schema: dict[str, Any]) -> tuple[FieldSpec, ...]:
    return tuple(_field_spec(name, value) for name, value in schema["fields"].items())


def _gap(
    *,
    code: str,
    target_schema: str,
    target: FieldSpec,
    candidates: tuple[str, ...] = (),
    message: str,
) -> DerivationGap:
    return DerivationGap(
        code=code,
        target_path=f"{target_schema}.{target.name}",
        semantic=target.semantic,
        required_type=target.type,
        required_authority=target.authority,
        candidates=candidates,
        message=message,
    )


def derive_capability_mapping(
    source_definition: dict[str, Any],
    source_capability: str,
    target_definition: dict[str, Any],
    target_capability: str,
) -> DerivationReport:
    """Derive an exact projection from source output to target input, or report semantic gaps."""
    source_schema_name, source_schema = _capability_schema(
        source_definition, source_capability, "output"
    )
    target_schema_name, target_schema = _capability_schema(
        target_definition, target_capability, "input"
    )
    source_fields = _fields(source_schema)
    target_fields = _fields(target_schema)

    mapping: list[MappingStep] = []
    gaps: list[DerivationGap] = []

    for target in target_fields:
        if target.type is None or target.semantic is None:
            missing = []
            if target.type is None:
                missing.append("type")
            if target.semantic is None:
                missing.append("semantic")
            gaps.append(
                _gap(
                    code="TARGET_FIELD_NOT_SELF_DESCRIBING",
                    target_schema=target_schema_name,
                    target=target,
                    message=(
                        f"target field must declare {', '.join(missing)}; "
                        "field-name inference is forbidden"
                    ),
                )
            )
            continue

        if target.mapping != "exact":
            gaps.append(
                _gap(
                    code="UNSUPPORTED_TRANSFORMATION",
                    target_schema=target_schema_name,
                    target=target,
                    message=(
                        f"target requests mapping={target.mapping!r}; "
                        "v0 only proves exact projections"
                    ),
                )
            )
            continue

        semantic_candidates = tuple(
            source for source in source_fields if source.semantic == target.semantic
        )
        if not semantic_candidates:
            same_name = tuple(source for source in source_fields if source.name == target.name)
            candidates = tuple(f"{source_schema_name}.{source.name}" for source in same_name)
            code = "SEMANTIC_NOT_DECLARED" if same_name else "SEMANTIC_SOURCE_NOT_FOUND"
            message = (
                "matching field name/type is not evidence; declare a source semantic id"
                if same_name
                else "no source field declares the required semantic id"
            )
            gaps.append(
                _gap(
                    code=code,
                    target_schema=target_schema_name,
                    target=target,
                    candidates=candidates,
                    message=message,
                )
            )
            continue

        type_candidates = tuple(
            source for source in semantic_candidates if source.type == target.type
        )
        if not type_candidates:
            gaps.append(
                _gap(
                    code="TYPE_MISMATCH",
                    target_schema=target_schema_name,
                    target=target,
                    candidates=tuple(
                        f"{source_schema_name}.{source.name}:{source.type or '?'}"
                        for source in semantic_candidates
                    ),
                    message="semantic id matches, but exact type compatibility is not proven",
                )
            )
            continue

        authority_candidates = tuple(
            source
            for source in type_candidates
            if target.authority is None or source.authority == target.authority
        )
        if not authority_candidates:
            gaps.append(
                _gap(
                    code="AUTHORITY_MISMATCH",
                    target_schema=target_schema_name,
                    target=target,
                    candidates=tuple(
                        f"{source_schema_name}.{source.name}@{source.authority or '?'}"
                        for source in type_candidates
                    ),
                    message="semantic and type match, but the required authority is not proven",
                )
            )
            continue

        if len(authority_candidates) != 1:
            gaps.append(
                _gap(
                    code="AMBIGUOUS_SEMANTIC_SOURCE",
                    target_schema=target_schema_name,
                    target=target,
                    candidates=tuple(
                        f"{source_schema_name}.{source.name}" for source in authority_candidates
                    ),
                    message=(
                        "more than one source field satisfies the declared semantic contract"
                    ),
                )
            )
            continue

        source = authority_candidates[0]
        mapping.append(
            MappingStep(
                source_path=f"{source_schema_name}.{source.name}",
                target_path=f"{target_schema_name}.{target.name}",
                semantic=target.semantic,
                type=target.type,
                authority=target.authority or source.authority,
            )
        )

    return DerivationReport(
        schema_version=REPORT_SCHEMA_VERSION,
        status="derived" if not gaps else "unresolved",
        source_capability=source_capability,
        source_schema=source_schema_name,
        target_capability=target_capability,
        target_schema=target_schema_name,
        mapping=tuple(mapping),
        gaps=tuple(gaps),
        language_rules=tuple(sorted(IMPLEMENTED_BOX_LANGUAGE_RULES)),
    )


def apply_exact_projection(
    report: DerivationReport,
    source_value: dict[str, Any],
) -> dict[str, Any]:
    """Apply a proven exact mapping. This helper performs no inference or authority decision."""
    if report.status != "derived" or report.gaps:
        raise BoxDerivabilityError("cannot execute an unresolved mapping")
    if not isinstance(source_value, dict):
        raise BoxDerivabilityError("source value must be a mapping")

    result: dict[str, Any] = {}
    for step in report.mapping:
        if step.operator != "exact_project":
            raise BoxDerivabilityError(f"unsupported compiled operator: {step.operator}")
        source_schema, separator, source_field = step.source_path.partition(".")
        target_schema, target_separator, target_field = step.target_path.partition(".")
        if (
            not separator
            or not target_separator
            or source_schema != report.source_schema
            or target_schema != report.target_schema
        ):
            raise BoxDerivabilityError("compiled mapping contains an invalid field path")
        if source_field not in source_value:
            raise BoxDerivabilityError(f"source value is missing required field: {source_field}")
        result[target_field] = source_value[source_field]
    return result


def render_json(report: DerivationReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def render_human(report: DerivationReport) -> str:
    lines = [
        f"Derivability: {report.status}",
        f"Source: {report.source_capability} -> {report.source_schema}",
        f"Target: {report.target_capability} <- {report.target_schema}",
        "Language rules: " + ", ".join(report.language_rules),
    ]
    if report.mapping:
        lines.append("")
        lines.append("Derived exact projections:")
        for step in report.mapping:
            suffix = f" @ {step.authority}" if step.authority else ""
            lines.append(
                f"- {step.source_path} -> {step.target_path} "
                f"[{step.semantic}: {step.type}{suffix}]"
            )
    if report.gaps:
        lines.append("")
        lines.append("Semantic gaps:")
        for gap in report.gaps:
            lines.append(f"- {gap.code}: {gap.target_path} — {gap.message}")
            if gap.candidates:
                lines.append(f"  candidates: {', '.join(gap.candidates)}")
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_manifest", type=Path)
    parser.add_argument("source_capability")
    parser.add_argument("target_manifest", type=Path)
    parser.add_argument("target_capability")
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        report = derive_capability_mapping(
            load_definition(args.source_manifest),
            args.source_capability,
            load_definition(args.target_manifest),
            args.target_capability,
        )
    except BoxDerivabilityError as exc:
        raise SystemExit(f"box derivability error: {exc}") from exc

    print(render_json(report) if args.as_json else render_human(report), end="")
    return 0 if report.status == "derived" else 2


if __name__ == "__main__":
    raise SystemExit(main())
