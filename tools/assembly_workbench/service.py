from __future__ import annotations

from pathlib import Path
from typing import Any

from assembly_workbench.checks import run
from assembly_workbench.model import CHECK_ORDER, INSPECTION_SCHEMA, REPORT_SCHEMA, AssemblyWorkbenchError

def _validate_project(project: Path) -> None:
    if not project.is_dir():
        raise AssemblyWorkbenchError(f"Project directory not found: {project}")

def inspect_check(project: Path, name: str, *, factory_root: Path | None = None) -> dict[str, Any]:
    _validate_project(project)
    check = run(project, name, factory_root=factory_root)
    return {
        "schema_version": INSPECTION_SCHEMA,
        "project_root": project.resolve().name,
        "check": check.to_dict(),
    }

def verify(project: Path, *, factory_root: Path | None = None) -> dict[str, Any]:
    _validate_project(project)
    checks = [run(project, name, factory_root=factory_root) for name in CHECK_ORDER]
    ready_checks = sum(check.ready for check in checks)
    errors = sum(check.errors for check in checks)
    warnings = sum(check.warnings for check in checks)
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project.resolve().name,
        "ready": ready_checks == len(checks),
        "summary": {
            "checks": len(checks),
            "ready_checks": ready_checks,
            "errors": errors,
            "warnings": warnings,
        },
        "checks": [check.to_dict(include_findings=False) for check in checks],
    }
