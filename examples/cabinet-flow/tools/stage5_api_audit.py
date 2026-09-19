#!/usr/bin/env python3
"""Deterministic structural audit for Cabinet Flow State 5 public operations."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

REQUIRED_HEADINGS = (
    "Owner",
    "Callers",
    "Inputs",
    "Outputs",
    "Observable effect",
    "Enforces",
    "Errors",
    "State impact",
)
TOKEN_RE = re.compile(r"`((?:module|boundary):[^`]+)`")
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|FIXME|TBD)\b|\?\?\?", re.IGNORECASE)


@dataclass
class Section:
    key: str
    path: Path
    start_line: int
    lines: list[str]

    @property
    def body(self) -> str:
        return "\n".join(self.lines)

    def subsection(self, name: str) -> str | None:
        marker = f"### {name}"
        for index, line in enumerate(self.lines):
            if line != marker:
                continue
            start = index + 1
            while start < len(self.lines) and self.lines[start] == "":
                start += 1
            end = start
            while end < len(self.lines) and not self.lines[end].startswith("### "):
                end += 1
            return "\n".join(self.lines[start:end]).strip()
        return None


def parse_sections(path: Path) -> list[Section]:
    lines = path.read_text(encoding="utf-8").splitlines()
    sections: list[Section] = []
    current_key: str | None = None
    current_start = 0
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_start, current_lines
        if current_key is not None:
            sections.append(Section(current_key, path, current_start, current_lines))
        current_key = None
        current_lines = []

    for index, line in enumerate(lines, start=1):
        match = re.fullmatch(r"## `(public_op:[^`]+)`", line)
        if match:
            flush()
            current_key = match.group(1)
            current_start = index
            continue
        if current_key is not None:
            current_lines.append(line)
    flush()
    return sections


def audit(project: Path) -> list[str]:
    plan_path = project / "50_api_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    operations = plan.get("public_operations") or plan.get("operations") or []
    expected = {item["key"]: item for item in operations}
    findings: list[str] = []

    if len(expected) != len(operations):
        findings.append("50_api_plan.json: duplicate operation keys in plan")

    by_key: dict[str, list[Section]] = {}
    for path in sorted(project.glob("50_public_apis_*.md")):
        for section in parse_sections(path):
            by_key.setdefault(section.key, []).append(section)

    for key, sections in sorted(by_key.items()):
        if key not in expected:
            for section in sections:
                findings.append(f"{section.path.name}:{section.start_line}: extra unplanned {key}")
        if len(sections) > 1:
            locations = ", ".join(f"{s.path.name}:{s.start_line}" for s in sections)
            findings.append(f"{key}: documented more than once: {locations}")

    for key, item in sorted(expected.items()):
        sections = by_key.get(key, [])
        if not sections:
            findings.append(f"{key}: missing Stage 5 section")
            continue
        if len(sections) != 1:
            continue
        section = sections[0]

        for heading in REQUIRED_HEADINGS:
            if section.subsection(heading) is None:
                findings.append(
                    f"{section.path.name}:{section.start_line}: {key}: missing ### {heading}"
                )

        owner_text = section.subsection("Owner") or ""
        expected_owner = f"module:{key.split(':', 1)[1].split('.', 1)[0]}"
        owner_tokens = set(TOKEN_RE.findall(owner_text))
        if expected_owner not in owner_tokens:
            findings.append(
                f"{section.path.name}:{section.start_line}: {key}: owner must name {expected_owner}; got {sorted(owner_tokens)}"
            )

        callers_text = section.subsection("Callers") or ""
        actual_callers = set(TOKEN_RE.findall(callers_text))
        expected_callers = set(item.get("callers") or [])
        if actual_callers != expected_callers:
            findings.append(
                f"{section.path.name}:{section.start_line}: {key}: callers mismatch; "
                f"plan={sorted(expected_callers)} doc={sorted(actual_callers)}"
            )

        placeholder = PLACEHOLDER_RE.search(section.body)
        if placeholder:
            findings.append(
                f"{section.path.name}:{section.start_line}: {key}: placeholder marker {placeholder.group(0)!r}"
            )

    if len(expected) != 95:
        findings.append(
            f"50_api_plan.json: expected frozen Stage 5 count 95, found {len(expected)}; "
            "update this audit intentionally if the architecture adds/removes operations"
        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path, help="Path to examples/cabinet-flow")
    args = parser.parse_args()

    project = args.project.resolve()
    findings = audit(project)
    if findings:
        for finding in findings:
            print(finding)
        print(f"FAIL: {len(findings)} Stage 5 consistency finding(s)")
        return 1
    print("PASS: Cabinet Flow Stage 5 API audit (95/95, owners/callers/headings consistent)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
