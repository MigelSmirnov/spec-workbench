#!/usr/bin/env python3
"""The deterministic-backend binding step of the authoring sequence.

A port interface given ``disposition: local`` must resolve to a registered
deterministic emitter — the factory's canonical rule
``local_implementation_requires_deterministic_backend`` blocks generation
otherwise, and by then the decision is weeks old. This step runs the same
rule at authoring time, through the factory's own catalog binder
(``tools/emitter_catalog.py --spec``), and shows both decisions at once:
that the port needs a deterministic block, and the exact closed IR form to
author (the catalog card's ``ir_skeleton``).

Authority stays with the factory: this tool never restates a schema. When
the sibling factory checkout or its catalog tool is unavailable, the step
reports that and stands aside — the factory validator remains the judge at
admission.

    python tools/design_emitter_binding.py examples/<case> --coverage [--json]
"""
from __future__ import annotations

import argparse
import fence
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "spec_workbench_emitter_binding.v1"
FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"
CATALOG_TOOL = "tools/emitter_catalog.py"
ASSEMBLED_SPEC_FILE = "global_spec.json"


def factory_root(workbench_root: Path) -> Path:
    override = os.environ.get(FACTORY_ROOT_ENV)
    return Path(override) if override else workbench_root.parent / "code_factory"


def run_binding(spec_path: Path, factory: Path) -> dict[str, Any] | None:
    """The factory's catalog binder over one spec; None when unavailable."""
    tool = factory / CATALOG_TOOL
    if not tool.is_file():
        return None
    result = subprocess.run(
        [sys.executable, str(tool), "--spec", str(spec_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1) or not result.stdout.strip():
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def coverage(project: Path, factory: Path | None = None) -> dict[str, Any]:
    project = project.resolve()
    if factory is None:
        workbench_root = Path(__file__).resolve().parents[1]
        factory = factory_root(workbench_root)
    spec_path = project / ASSEMBLED_SPEC_FILE
    findings: list[dict[str, Any]] = []
    catalog_available = False
    unbound = 0
    if not spec_path.is_file():
        # nothing assembled yet: the step has nothing to bind and stands aside
        report = None
    else:
        report = run_binding(spec_path, factory)
    if report is None and spec_path.is_file():
        findings.append({
            "severity": "warning",
            "code": "factory_catalog_unavailable",
            "message": (
                f"factory catalog binder not available at {factory / CATALOG_TOOL}; "
                "deterministic-backend binding will be judged only at factory admission (FA005)"
            ),
        })
    elif report is not None:
        catalog_available = True
        for port in report.get("unbound_ports", []):
            unbound += 1
            findings.append({
                "severity": "error",
                "code": "local_port_without_deterministic_backend",
                "interface": port.get("interface"),
                "concrete": port.get("concrete"),
                "module": port.get("module"),
                "direction": port.get("direction"),
                "catalog_card": port.get("catalog_card"),
                "message": (
                    f"{port.get('interface')}: {port.get('direction')}"
                ),
            })
    return {
        "schema_version": SCHEMA_VERSION,
        "project_root": project.name,
        "summary": {
            "catalog_available": catalog_available,
            "unbound_ports": unbound,
            "errors": unbound,
            "handoff_ready": unbound == 0,
        },
        "findings": fence.enforce(findings),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project", type=Path)
    parser.add_argument("--coverage", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--factory-root", type=Path)
    args = parser.parse_args(argv)
    if not args.project.is_dir():
        print(f"design_emitter_binding: error: project directory not found: {args.project}", file=sys.stderr)
        return 2
    report = coverage(args.project, args.factory_root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        summary = report["summary"]
        print(f"Deterministic backend binding: unbound={summary['unbound_ports']} "
              f"catalog={'yes' if summary['catalog_available'] else 'unavailable'} "
              f"handoff_ready={str(summary['handoff_ready']).lower()}")
        for finding in report["findings"]:
            print(f"  {'✗' if finding['severity'] == 'error' else '!'} {finding['message']}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
