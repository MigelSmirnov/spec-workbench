#!/usr/bin/env python3
"""Validate deterministic API assembly constraints in global_spec.json.

The HTTP ``api`` artifact is compiler-owned. Project specs may declare only the
explicit provider-function exposure manifest at
``imports.module_internal.api``. This linter is structural and fail-closed; it
does not infer endpoint semantics or business policy from names/prose.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "spec_workbench_api_lint.v1"
NOTE_RE = re.compile(r"^(?P<target>[A-Za-z_][A-Za-z0-9_.]*):")


def _finding(code: str, message: str, *, path: str) -> dict[str, str]:
    return {"severity": "error", "code": code, "path": path, "message": message}


def lint(spec: dict[str, Any]) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    module_functions = spec.get("module_functions") or {}
    module_paths = spec.get("module_paths") or {}
    module_order = spec.get("module_order") or []
    default_module = spec.get("default_module")
    contracts = spec.get("contracts") or {}
    notes = spec.get("notes") or []
    imports = spec.get("imports") or {}
    internal = imports.get("internal") or {}
    module_internal = imports.get("module_internal") or {}

    if "api" in module_functions:
        findings.append(_finding(
            "api_project_module_declared",
            "compiler-owned api MUST NOT appear in module_functions",
            path="module_functions.api",
        ))
    if "api" in module_paths:
        findings.append(_finding(
            "api_project_path_declared",
            "compiler-owned api MUST NOT appear in module_paths",
            path="module_paths.api",
        ))
    if isinstance(module_order, list) and "api" in module_order:
        findings.append(_finding(
            "api_project_order_declared",
            "compiler-owned api MUST NOT appear in module_order",
            path="module_order",
        ))
    if default_module == "api":
        findings.append(_finding(
            "api_is_default_module",
            "compiler-owned api MUST NOT be default_module",
            path="default_module",
        ))
    if isinstance(internal, dict) and "api" in internal:
        findings.append(_finding(
            "api_internal_export_declared",
            "compiler-owned api MUST NOT define imports.internal exports",
            path="imports.internal.api",
        ))

    if isinstance(module_internal, dict):
        for consumer, providers in module_internal.items():
            if consumer == "api" or not isinstance(providers, dict):
                continue
            if "api" in providers:
                findings.append(_finding(
                    "project_module_depends_on_api",
                    f"project module {consumer!r} MUST NOT depend on compiler-owned api",
                    path=f"imports.module_internal.{consumer}.api",
                ))

    for index, note in enumerate(notes if isinstance(notes, list) else []):
        if not isinstance(note, str):
            continue
        match = NOTE_RE.match(note)
        if match and match.group("target") == "api":
            findings.append(_finding(
                "api_module_note_declared",
                "finalized specs MUST NOT contain project-owned module-level api: notes",
                path=f"notes[{index}]",
            ))

    exposures = module_internal.get("api", {}) if isinstance(module_internal, dict) else {}
    if exposures is None:
        exposures = {}
    if not isinstance(exposures, dict):
        findings.append(_finding(
            "api_exposure_manifest_not_object",
            "imports.module_internal.api MUST be a provider->symbols object",
            path="imports.module_internal.api",
        ))
        exposures = {}

    exposed_count = 0
    for provider, symbols in exposures.items():
        provider_path = f"imports.module_internal.api.{provider}"
        if provider == "api":
            findings.append(_finding(
                "api_self_dependency",
                "api exposure manifest MUST NOT name api as a provider",
                path=provider_path,
            ))
            continue
        if provider not in module_functions:
            findings.append(_finding(
                "api_unknown_provider",
                f"API exposure provider {provider!r} is absent from module_functions",
                path=provider_path,
            ))
        if not isinstance(symbols, list) or not all(isinstance(item, str) for item in symbols):
            findings.append(_finding(
                "api_exposure_symbols_not_list",
                "API exposure provider value MUST be a list of symbol names",
                path=provider_path,
            ))
            continue
        duplicates = sorted({symbol for symbol in symbols if symbols.count(symbol) > 1})
        for symbol in duplicates:
            findings.append(_finding(
                "api_duplicate_exposure",
                f"API exposure contains duplicate symbol {symbol!r}",
                path=provider_path,
            ))
        provider_members = set(module_functions.get(provider, []) or [])
        provider_exports = set(internal.get(provider, []) or []) if isinstance(internal, dict) else set()
        for symbol in symbols:
            exposed_count += 1
            symbol_path = f"{provider_path}.{symbol}"
            if symbol.startswith("_"):
                findings.append(_finding(
                    "api_private_symbol_exposed",
                    f"private symbol {symbol!r} MUST NOT be exposed through deterministic api",
                    path=symbol_path,
                ))
            if symbol not in provider_members:
                findings.append(_finding(
                    "api_symbol_not_owned_by_provider",
                    f"exposed symbol {symbol!r} is not owned by module {provider!r}",
                    path=symbol_path,
                ))
            if symbol not in provider_exports:
                findings.append(_finding(
                    "api_symbol_not_public_export",
                    f"exposed symbol {symbol!r} is absent from imports.internal[{provider!r}]",
                    path=symbol_path,
                ))
            if symbol not in contracts:
                findings.append(_finding(
                    "api_symbol_not_function_contract",
                    f"exposed symbol {symbol!r} must have a top-level function contract",
                    path=symbol_path,
                ))
            if any(key.startswith(f"{symbol}.") for key in contracts):
                findings.append(_finding(
                    "api_class_symbol_exposed",
                    f"class-like symbol {symbol!r} MUST NOT be directly exposed as an API operation",
                    path=symbol_path,
                ))

    return {
        "schema_version": SCHEMA_VERSION,
        "summary": {
            "errors": len(findings),
            "exposed_operations": exposed_count,
            "providers": len(exposures),
        },
        "findings": findings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        payload = json.loads(args.spec.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"spec_api_lint: error: {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print("spec_api_lint: error: spec root must be an object", file=sys.stderr)
        return 2
    report = lint(payload)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"API assembly: {summary['exposed_operations']} exposed operations; {summary['errors']} errors")
        for finding in report["findings"]:
            print(f"ERROR {finding['code']} {finding['path']} - {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
