#!/usr/bin/env python3
"""Deterministic State 3 module structure, lint, and handoff.

This tool owns only State 3 structure. Module headings become stable
``module:<name>`` keys and candidate public capabilities become stable
``capability:<module>.<operation>`` keys. Cross-state ownership and coverage are
owned by ``design_trace.py`` and its explicit trace manifest.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "spec_workbench_state3.v2"
HANDOFF_SCHEMA = "spec_workbench_state3_handoff.v2"
LINT_SCHEMA = "spec_workbench_state3_lint.v2"
MODULE_RE = re.compile(r"^`(?P<name>[a-z][a-z0-9_]*)`$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATE3_RE = re.compile(r"\bState\s+3\b", re.IGNORECASE)
IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REQUIRED_SECTIONS = ("Owns", "Knows", "Must not own", "Depth assessment")
CAPABILITY_SECTIONS = ("Candidate public capabilities", "Public surface")
GENERIC_MODULE_NAMES = {"utils", "helpers", "manager", "processor", "service", "common"}


@dataclass(frozen=True)
class SourceRange:
    path: str
    start_line: int
    end_line: int


@dataclass(frozen=True)
class ModuleItem:
    key: str
    name: str
    source: SourceRange
    sections: tuple[str, ...]
    capabilities: tuple[str, ...]


@dataclass(frozen=True)
class Finding:
    severity: str
    code: str
    module_key: str
    message: str
    source: SourceRange


def _iter_state3_files(project: Path) -> Iterable[Path]:
    for path in sorted(project.rglob("*.md")):
        if not path.is_file():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        if any(STATE3_RE.search(line) for line in lines[:40]):
            yield path


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    result: list[tuple[int, int, str]] = []
    for number, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            result.append((number, len(match.group(1)), match.group(2).strip()))
    return result


def _section_range(
    headings: list[tuple[int, int, str]],
    *,
    module_start: int,
    module_end: int,
    title: str,
) -> tuple[int, int] | None:
    wanted = title.casefold()
    for index, (start, level, heading_title) in enumerate(headings):
        if not (module_start < start <= module_end):
            continue
        if heading_title.casefold() != wanted:
            continue
        end = module_end
        for next_start, next_level, _ in headings[index + 1 :]:
            if next_start > module_end:
                break
            if next_level <= level:
                end = next_start - 1
                break
        return start, end
    return None


def _extract_capabilities(
    lines: list[str],
    headings: list[tuple[int, int, str]],
    start: int,
    end: int,
) -> tuple[str, ...]:
    result: set[str] = set()
    for title in CAPABILITY_SECTIONS:
        section = _section_range(
            headings,
            module_start=start,
            module_end=end,
            title=title,
        )
        if section is None:
            continue
        section_start, section_end = section
        in_fence = False
        for raw in lines[section_start:section_end]:
            stripped = raw.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                continue
            candidate = stripped.strip("`*- ")
            if IDENT_RE.fullmatch(candidate):
                result.add(candidate)
    return tuple(sorted(result))


def _capability_refs(module: ModuleItem) -> list[dict[str, str]]:
    return [
        {"key": f"capability:{module.name}.{name}", "name": name}
        for name in module.capabilities
    ]


def _module_payload(module: ModuleItem) -> dict[str, object]:
    payload = asdict(module)
    payload["capability_refs"] = _capability_refs(module)
    return payload


def parse_modules(project: Path) -> list[ModuleItem]:
    project = project.resolve()
    result: list[ModuleItem] = []
    for path in _iter_state3_files(project):
        lines = path.read_text(encoding="utf-8").splitlines()
        headings = _headings(lines)
        for index, (start, level, title) in enumerate(headings):
            if level != 2:
                continue
            match = MODULE_RE.fullmatch(title)
            if match is None:
                continue
            end = len(lines)
            for next_start, next_level, _ in headings[index + 1 :]:
                if next_level <= level:
                    end = next_start - 1
                    break
            child_titles = tuple(
                child_title
                for child_start, child_level, child_title in headings[index + 1 :]
                if start < child_start <= end and child_level > level
            )
            name = match.group("name")
            result.append(
                ModuleItem(
                    key=f"module:{name}",
                    name=name,
                    source=SourceRange(path.relative_to(project).as_posix(), start, end),
                    sections=child_titles,
                    capabilities=_extract_capabilities(lines, headings, start, end),
                )
            )
    return result


def manifest(project: Path) -> dict[str, object]:
    modules = parse_modules(project)
    counts: dict[str, int] = {}
    for module in modules:
        counts[module.key] = counts.get(module.key, 0) + 1
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": project.resolve().name,
        "modules": [_module_payload(module) for module in modules],
        "diagnostics": {
            "duplicate_module_keys": sorted(key for key, count in counts.items() if count > 1)
        },
    }


def get_module(project: Path, key: str) -> dict[str, object] | None:
    normalized = key if key.startswith("module:") else f"module:{key}"
    for module in parse_modules(project):
        if module.key == normalized:
            return _module_payload(module)
    return None


def handoff(project: Path) -> dict[str, object]:
    modules = parse_modules(project)
    capabilities: list[dict[str, str]] = []
    module_payloads: list[dict[str, object]] = []
    for module in modules:
        refs = _capability_refs(module)
        module_payloads.append(
            {
                "key": module.key,
                "name": module.name,
                "capabilities": list(module.capabilities),
                "capability_refs": refs,
            }
        )
        capabilities.extend(
            {"key": ref["key"], "name": ref["name"], "module": module.key}
            for ref in refs
        )
    return {
        "schema_version": HANDOFF_SCHEMA,
        "modules": module_payloads,
        "capabilities": capabilities,
    }


def lint(project: Path) -> dict[str, object]:
    modules = parse_modules(project)
    findings: list[Finding] = []
    counts: dict[str, int] = {}
    for module in modules:
        counts[module.key] = counts.get(module.key, 0) + 1

    for module in modules:
        normalized_sections = {title.casefold() for title in module.sections}
        if counts[module.key] > 1:
            findings.append(
                Finding("error", "duplicate_module_key", module.key, "Module key is not unique.", module.source)
            )
        for required in REQUIRED_SECTIONS:
            if required.casefold() not in normalized_sections:
                findings.append(
                    Finding(
                        "error",
                        "missing_module_section",
                        module.key,
                        f"Required State 3 section {required!r} is absent.",
                        module.source,
                    )
                )
        if "hides" not in normalized_sections and module.name != "domain_models":
            findings.append(
                Finding(
                    "warning",
                    "missing_hides_section",
                    module.key,
                    "Deep runtime module should state what complexity it hides.",
                    module.source,
                )
            )
        if not module.capabilities and module.name != "domain_models":
            findings.append(
                Finding(
                    "warning",
                    "missing_capabilities",
                    module.key,
                    "Runtime responsibility exposes no machine-readable candidate capability names.",
                    module.source,
                )
            )
        if module.name in GENERIC_MODULE_NAMES:
            findings.append(
                Finding(
                    "error",
                    "generic_module_name",
                    module.key,
                    "Generic module name does not identify a stable responsibility.",
                    module.source,
                )
            )

    return {
        "schema_version": LINT_SCHEMA,
        "summary": {
            "modules": len(modules),
            "errors": sum(finding.severity == "error" for finding in findings),
            "warnings": sum(finding.severity == "warning" for finding in findings),
        },
        "findings": [asdict(finding) for finding in findings],
    }


def _render_human(payload: dict[str, object]) -> str:
    summary = payload["summary"]
    lines = [
        "State 3: "
        f"{summary['modules']} modules; {summary['errors']} errors; "
        f"{summary['warnings']} warnings"
    ]
    for finding in payload["findings"]:
        lines.append(
            f"{finding['severity'].upper()} {finding['code']} "
            f"{finding['module_key']} - {finding['message']}"
        )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--list", action="store_true")
    action.add_argument("--get", metavar="MODULE_KEY")
    action.add_argument("--handoff", action="store_true")
    action.add_argument("--lint", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.project.is_dir():
        print(f"design_stage3: error: project directory not found: {args.project}", file=sys.stderr)
        return 2

    if args.get:
        payload = get_module(args.project, args.get)
        if payload is None:
            print(f"design_stage3: error: unknown module: {args.get}", file=sys.stderr)
            return 1
    elif args.handoff:
        payload = handoff(args.project)
    elif args.lint:
        payload = lint(args.project)
    elif args.list:
        payload = [_module_payload(module) for module in parse_modules(args.project)]
    else:
        payload = manifest(args.project)

    if args.lint and not args.json:
        print(_render_human(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    if args.lint and payload["summary"]["errors"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
