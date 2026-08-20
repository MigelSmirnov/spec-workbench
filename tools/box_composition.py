#!/usr/bin/env python3
"""Compile and execute disposable cross-box projections from self-described manifests."""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from box_derivability import (
    BoxDerivabilityError,
    DerivationReport,
    apply_exact_projection,
    derive_capability_mapping,
    load_definition,
)


PLAN_SCHEMA_VERSION = "spec_workbench_box_composition.v0"


@dataclass(frozen=True)
class CompositionNode:
    id: str
    operator: str
    capability: str | None
    input_schema: str | None
    output_schema: str | None


@dataclass(frozen=True)
class CompositionPlan:
    schema_version: str
    status: str
    source_capability: str
    target_capability: str
    derivation: DerivationReport
    nodes: tuple[CompositionNode, ...]
    plan_digest: str


@dataclass(frozen=True)
class CompositionExecution:
    plan_digest: str
    result: dict[str, Any]
    trace: tuple[dict[str, str], ...]


def _digest(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(payload).hexdigest()


def compile_composition(
    source_definition: dict[str, Any],
    source_capability: str,
    target_definition: dict[str, Any],
    target_capability: str,
) -> CompositionPlan:
    """Compile the only mapping proved by the two manifests; never accept hand-written mapping."""
    derivation = derive_capability_mapping(
        source_definition,
        source_capability,
        target_definition,
        target_capability,
    )

    nodes = (
        CompositionNode(
            id="source",
            operator="invoke_capability",
            capability=source_capability,
            input_schema=None,
            output_schema=derivation.source_schema,
        ),
        CompositionNode(
            id="projection",
            operator="exact_project",
            capability=None,
            input_schema=derivation.source_schema,
            output_schema=derivation.target_schema,
        ),
        CompositionNode(
            id="target",
            operator="invoke_capability",
            capability=target_capability,
            input_schema=derivation.target_schema,
            output_schema=None,
        ),
    )

    digest_input = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "status": derivation.status,
        "source_capability": source_capability,
        "target_capability": target_capability,
        "derivation": asdict(derivation),
        "nodes": [asdict(node) for node in nodes],
    }
    return CompositionPlan(
        schema_version=PLAN_SCHEMA_VERSION,
        status=derivation.status,
        source_capability=source_capability,
        target_capability=target_capability,
        derivation=derivation,
        nodes=nodes,
        plan_digest=_digest(digest_input),
    )


def execute_composition(
    plan: CompositionPlan,
    source_invoke: Callable[[str, dict[str, Any]], dict[str, Any]],
    target_invoke: Callable[[str, dict[str, Any]], dict[str, Any]],
    *,
    source_args: dict[str, Any] | None = None,
) -> CompositionExecution:
    """Execute a precompiled proof. Authority remains with each invoked box host."""
    if plan.status != "derived" or plan.derivation.gaps:
        raise BoxDerivabilityError("cannot execute an unresolved composition")

    source_args = {} if source_args is None else source_args
    if not isinstance(source_args, dict):
        raise BoxDerivabilityError("source args must be a mapping")

    # All derivability checks happen before either callback is invoked. An
    # unresolved target therefore cannot cause a source-side effect by accident.
    source_value = source_invoke(plan.source_capability, source_args)
    if not isinstance(source_value, dict):
        raise BoxDerivabilityError("source capability result must be a mapping")

    projected = apply_exact_projection(plan.derivation, source_value)
    result = target_invoke(plan.target_capability, projected)
    if not isinstance(result, dict):
        raise BoxDerivabilityError("target capability result must be a mapping")

    trace = (
        {
            "node": "source",
            "operator": "invoke_capability",
            "value_digest": _digest(source_value),
        },
        {
            "node": "projection",
            "operator": "exact_project",
            "value_digest": _digest(projected),
        },
        {
            "node": "target",
            "operator": "invoke_capability",
            "value_digest": _digest(result),
        },
    )
    return CompositionExecution(plan_digest=plan.plan_digest, result=result, trace=trace)


def render_json(plan: CompositionPlan) -> str:
    return json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n"


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
        plan = compile_composition(
            load_definition(args.source_manifest),
            args.source_capability,
            load_definition(args.target_manifest),
            args.target_capability,
        )
    except BoxDerivabilityError as exc:
        raise SystemExit(f"box composition error: {exc}") from exc

    if args.as_json:
        print(render_json(plan), end="")
    else:
        print(f"Composition: {plan.status}")
        print(f"Plan digest: {plan.plan_digest}")
        for node in plan.nodes:
            capability = f" {node.capability}" if node.capability else ""
            print(f"- {node.id}: {node.operator}{capability}")
        for gap in plan.derivation.gaps:
            print(f"- gap {gap.code}: {gap.target_path} — {gap.message}")
    return 0 if plan.status == "derived" else 2


if __name__ == "__main__":
    raise SystemExit(main())
