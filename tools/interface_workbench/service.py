"""Deterministic closure checks for spec-declared interfaces.

An interface may be injected as a dependency, produced as a return value, or
adapted by a transport handler from a transport-owned value.  The first case is
closed structurally by ``implementation_obligations``.  The latter two remain
LLM-owned boundaries and therefore need explicit State 7 construction guidance.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from notes_workbench.language import signature_parameters, signature_return


def _annotation_mentions(annotation: str, type_name: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9_]){re.escape(type_name)}(?![A-Za-z0-9_])",
        annotation,
    ) is not None


def interface_names(spec: dict[str, Any]) -> set[str]:
    models = spec.get("models")
    if not isinstance(models, dict):
        return set()
    return {
        name
        for name, declaration in models.items()
        if isinstance(name, str)
        and isinstance(declaration, dict)
        and declaration.get("kind") == "interface"
    }


def _interface_methods(
    contracts: dict[str, Any], interfaces: set[str]
) -> dict[str, dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for interface in interfaces:
        prefix = interface + "."
        result[interface] = {
            name[len(prefix) :]: signature
            for name, signature in contracts.items()
            if isinstance(name, str)
            and name.startswith(prefix)
            and isinstance(signature, str)
        }
    return result


def implementation_obligation_findings(spec: dict[str, Any]) -> dict[str, Any]:
    """Evaluate structural dispositions for interface-typed parameters."""
    contracts = spec.get("contracts", {})
    models = spec.get("models", {})
    if not isinstance(contracts, dict) or not isinstance(models, dict):
        return {
            "interfaces": [],
            "dependency_uses": {},
            "findings": [{"code": "malformed_contracts_or_models"}],
        }

    interfaces = interface_names(spec)
    dependency_uses: dict[str, list[str]] = {name: [] for name in interfaces}
    for owner, signature in contracts.items():
        if not isinstance(owner, str) or not isinstance(signature, str):
            continue
        owner_class = owner.split(".", 1)[0] if "." in owner else None
        for _parameter, annotation in signature_parameters(signature):
            for interface in interfaces:
                if owner_class != interface and _annotation_mentions(annotation, interface):
                    dependency_uses[interface].append(owner)
    dependency_uses = {
        name: sorted(set(uses))
        for name, uses in dependency_uses.items()
        if uses
    }

    obligations = spec.get("implementation_obligations")
    if not isinstance(obligations, dict):
        obligations = {}
    findings: list[dict[str, Any]] = []
    for interface in sorted(set(obligations) - interfaces):
        findings.append({
            "code": "unknown_interface_obligation",
            "interface": interface,
        })

    module_functions = spec.get("module_functions") or {}
    declared_classes = {
        symbol
        for symbols in module_functions.values()
        if isinstance(symbols, list)
        for symbol in symbols
        if isinstance(symbol, str)
        and any(name.startswith(symbol + ".") for name in contracts)
    } if isinstance(module_functions, dict) else set()
    methods = _interface_methods(contracts, interfaces)

    for interface, uses in sorted(dependency_uses.items()):
        row = obligations.get(interface)
        if not isinstance(row, dict):
            findings.append({
                "code": "missing_implementation_disposition",
                "interface": interface,
                "used_by": uses,
            })
            continue
        disposition = row.get("disposition")
        implementations = row.get("implementations", [])
        if disposition not in {"local", "policy", "external"}:
            findings.append({
                "code": "invalid_implementation_disposition",
                "interface": interface,
                "disposition": disposition,
            })
            continue
        if disposition == "external":
            if implementations not in (None, []):
                findings.append({
                    "code": "external_disposition_has_local_classes",
                    "interface": interface,
                })
            continue
        if not isinstance(implementations, list) or not implementations:
            findings.append({
                "code": "local_disposition_has_no_classes",
                "interface": interface,
            })
            continue
        for concrete in implementations:
            if (
                not isinstance(concrete, str)
                or concrete not in declared_classes
                or concrete in interfaces
            ):
                findings.append({
                    "code": "unknown_concrete_implementation",
                    "interface": interface,
                    "concrete": concrete,
                })
                continue
            for method, expected in sorted(methods[interface].items()):
                concrete_contract = f"{concrete}.{method}"
                actual = contracts.get(concrete_contract)
                if actual is None:
                    findings.append({
                        "code": "missing_concrete_method_contract",
                        "interface": interface,
                        "concrete": concrete,
                        "method": method,
                        "expected_contract": expected,
                    })
                elif actual != expected:
                    findings.append({
                        "code": "incompatible_concrete_method_contract",
                        "interface": interface,
                        "concrete": concrete,
                        "method": method,
                        "expected_contract": expected,
                        "actual_contract": actual,
                    })
    return {
        "interfaces": sorted(interfaces),
        "dependency_uses": dependency_uses,
        "findings": findings,
    }


def _has_concrete_guidance(text: str, interface: str) -> bool:
    if not _annotation_mentions(text, interface):
        return False
    return re.search(r"\b(?:concrete|adapter|implementation)\b", text, re.IGNORECASE) is not None


def _forbids_interface_instantiation(text: str, interface: str) -> bool:
    return re.search(
        rf"\bMUST\s+NOT\s+(?:directly\s+)?(?:instantiate|construct|call)\s+"
        rf"(?:the\s+)?{re.escape(interface)}(?:\s+interface)?\b",
        text,
        re.IGNORECASE,
    ) is not None


def construction_boundary_findings(
    spec: dict[str, Any], notes: Iterable[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Find LLM-owned interface producers/adapters without closed guidance."""
    contracts = spec.get("contracts")
    if not isinstance(contracts, dict):
        return [{"code": "malformed_contracts", "severity": "block"}]
    interfaces = interface_names(spec)
    by_scope: dict[str, list[dict[str, Any]]] = {}
    for note in notes:
        scope = note.get("scope")
        if isinstance(scope, str):
            by_scope.setdefault(scope, []).append(note)

    boundaries: set[tuple[str, str, str]] = set()
    for scope, signature in contracts.items():
        if not isinstance(scope, str) or not isinstance(signature, str):
            continue
        owner_class = scope.split(".", 1)[0] if "." in scope else None
        if owner_class in interfaces:
            continue
        parameters = [annotation for _name, annotation in signature_parameters(signature)]
        returned = signature_return(signature)
        for interface in interfaces:
            injected = any(_annotation_mentions(annotation, interface) for annotation in parameters)
            if _annotation_mentions(returned, interface):
                boundaries.add((scope, interface, "producer"))
            if injected or _annotation_mentions(returned, interface):
                continue
            if scope.endswith("_handler") and any(
                _annotation_mentions(str(note.get("text", "")), interface)
                for note in by_scope.get(scope, [])
            ):
                boundaries.add((scope, interface, "adapter"))

    findings: list[dict[str, Any]] = []
    for scope, interface, boundary in sorted(boundaries):
        texts = [str(note.get("text", "")) for note in by_scope.get(scope, [])]
        concrete = any(_has_concrete_guidance(text, interface) for text in texts)
        forbidden = any(_forbids_interface_instantiation(text, interface) for text in texts)
        if concrete and forbidden:
            continue
        missing = []
        if not concrete:
            missing.append("concrete implementation or adapter ownership")
        if not forbidden:
            missing.append(f"an explicit MUST NOT instantiate {interface} prohibition")
        findings.append({
            "severity": "block",
            "code": "interface_construction_not_closed",
            "scope": scope,
            "interface": interface,
            "boundary": boundary,
            "missing": missing,
            "message": (
                f"{scope} is an interface {boundary} boundary for {interface}; "
                f"State 7 notes must close {' and '.join(missing)}."
            ),
        })
    return findings
