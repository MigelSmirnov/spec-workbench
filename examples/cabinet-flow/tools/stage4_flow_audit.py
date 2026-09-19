#!/usr/bin/env python3
"""Cabinet Flow State 4 coverage and State 4 -> State 5 lineage audit."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FLOW_HEADING_RE = re.compile(r"^## `(?P<key>flow:[a-z][a-z0-9_]*)`$")
MODULE_RE = re.compile(r"`(module:[a-z][a-z0-9_]*)`")
CAPABILITY_RE = re.compile(r"`(capability:[a-z][a-z0-9_]*.[a-z][a-z0-9_]*)`")
REQUIRED_SECTIONS = ("Trigger", "Boundary", "Steps", "Outcomes", "Errors")
FROZEN_FLOW_COUNT = 13
FROZEN_CAPABILITY_COUNT = 95


def _parse_flows(path: Path) -> dict[str, dict[str, object]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    starts: list[tuple[str, int]] = []
    for index, line in enumerate(lines):
        match = FLOW_HEADING_RE.fullmatch(line)
        if match:
            starts.append((match.group("key"), index))

    result: dict[str, dict[str, object]] = {}
    for offset, (key, start) in enumerate(starts):
        end = starts[offset + 1][1] if offset + 1 < len(starts) else len(lines)
        block_lines = lines[start:end]
        body = "\n".join(block_lines)
        sections = {
            line.removeprefix("### ").strip()
            for line in block_lines
            if line.startswith("### ")
        }
        result[key] = {
            "sections": sections,
            "modules": set(MODULE_RE.findall(body)),
            "capabilities": set(CAPABILITY_RE.findall(body)),
        }
    return result


def audit(project: Path) -> list[str]:
    project = project.resolve()
    flow_plan = json.loads((project / "40_flow_plan.json").read_text(encoding="utf-8"))
    api_plan = json.loads((project / "50_api_plan.json").read_text(encoding="utf-8"))
    actual = _parse_flows(project / "40_flows.md")

    planned = flow_plan.get("flows") or []
    operations = api_plan.get("public_operations") or api_plan.get("operations") or []
    findings: list[str] = []

    planned_keys = [entry.get("key") for entry in planned]
    if len(planned_keys) != len(set(planned_keys)):
        findings.append("40_flow_plan.json: duplicate flow keys")
    if len(planned) != FROZEN_FLOW_COUNT:
        findings.append(
            f"40_flow_plan.json: expected frozen flow count {FROZEN_FLOW_COUNT}, found {len(planned)}"
        )

    expected_keys = set(planned_keys)
    actual_keys = set(actual)
    for key in sorted(expected_keys - actual_keys):
        findings.append(f"{key}: planned flow is missing from 40_flows.md")
    for key in sorted(actual_keys - expected_keys):
        findings.append(f"{key}: reviewed flow is not declared in 40_flow_plan.json")

    usage: dict[str, set[str]] = {}
    for entry in planned:
        key = entry["key"]
        flow = actual.get(key)
        if flow is None:
            continue

        sections = flow["sections"]
        for required in REQUIRED_SECTIONS:
            if required not in sections:
                findings.append(f"{key}: missing required section ### {required}")

        expected_modules = set(entry.get("required_modules") or [])
        actual_modules = set(flow["modules"])
        if actual_modules != expected_modules:
            missing = sorted(expected_modules - actual_modules)
            extra = sorted(actual_modules - expected_modules)
            findings.append(
                f"{key}: module refs mismatch; missing={missing} extra={extra}"
            )

        expected_capabilities = set(entry.get("candidate_capabilities") or [])
        actual_capabilities = set(flow["capabilities"])
        if actual_capabilities != expected_capabilities:
            missing = sorted(expected_capabilities - actual_capabilities)
            extra = sorted(actual_capabilities - expected_capabilities)
            findings.append(
                f"{key}: capability refs mismatch; missing={missing} extra={extra}"
            )

        for capability in expected_capabilities:
            usage.setdefault(capability, set()).add(key)

    api_by_capability: dict[str, dict[str, object]] = {}
    for operation in operations:
        capability = operation.get("capability")
        if not isinstance(capability, str):
            findings.append(f"{operation.get('key')}: missing capability")
            continue
        if capability in api_by_capability:
            findings.append(f"{capability}: more than one Stage 5 operation owns capability")
        api_by_capability[capability] = operation

    flow_capabilities = set(usage)
    api_capabilities = set(api_by_capability)
    if len(flow_capabilities) != FROZEN_CAPABILITY_COUNT:
        findings.append(
            f"State 4: expected {FROZEN_CAPABILITY_COUNT} unique candidate capabilities, "
            f"found {len(flow_capabilities)}"
        )
    if len(api_capabilities) != FROZEN_CAPABILITY_COUNT:
        findings.append(
            f"State 5: expected {FROZEN_CAPABILITY_COUNT} unique public capabilities, "
            f"found {len(api_capabilities)}"
        )

    for capability in sorted(flow_capabilities - api_capabilities):
        findings.append(f"{capability}: used by State 4 but has no Stage 5 public operation")
    for capability in sorted(api_capabilities - flow_capabilities):
        findings.append(f"{capability}: Stage 5 operation is not used by any planned State 4 flow")

    for capability in sorted(flow_capabilities & api_capabilities):
        expected_flows = usage[capability]
        actual_flows = set(api_by_capability[capability].get("flows") or [])
        if actual_flows != expected_flows:
            findings.append(
                f"{capability}: flow lineage mismatch; "
                f"state4={sorted(expected_flows)} state5={sorted(actual_flows)}"
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path, help="Path to examples/cabinet-flow")
    args = parser.parse_args()

    findings = audit(args.project)
    if findings:
        for finding in findings:
            print(finding)
        print(f"FAIL: {len(findings)} State 4/5 lineage finding(s)")
        return 1
    print("PASS: Cabinet Flow State 4 coverage (13/13) and State 4->5 lineage (95/95)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
