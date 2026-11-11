"""Evidence from the accepted code (IMPORTS_WORKBENCH.md §8).

The Factory's own read-only report says which project symbols each module's
code names directly (``code_imports``). It runs in the Factory checkout as
factory_slice_workbench runs the Factory's tools: a subprocess, cwd at the
Factory root. Authority stays with the Factory; nothing here parses code.

- no 90_factory_target.json  -> not_applicable (a new project has no code);
- a target, but no Factory, no report or a report without code -> unavailable,
  which the gate turns into a block, never a skip.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from imports_workbench.model import AVAILABLE, NOT_APPLICABLE, UNAVAILABLE

FACTORY_ROOT_ENV = "SPEC_WORKBENCH_FACTORY_ROOT"
REPORT_TIMEOUT_SECONDS = 600
SLICER = Path("tools") / "slicer" / "__main__.py"
STRUCTURE = Path("project_index") / "structure.json"


def factory_root(project: Path, explicit: Path | None = None) -> tuple[Path | None, str]:
    """The Factory checkout and where it came from.

    A root the author names (--factory-root, then SPEC_WORKBENCH_FACTORY_ROOT) is
    final: when it has no slicer the evidence is unavailable, never a checkout
    found elsewhere. Only with neither is a sibling ``code_factory`` looked for.
    """
    named = Path(explicit) if explicit is not None else (
        Path(os.environ[FACTORY_ROOT_ENV]) if os.environ.get(FACTORY_ROOT_ENV) else None)
    if named is not None:
        source = "--factory-root" if explicit is not None else FACTORY_ROOT_ENV
        return (named.resolve() if (named / SLICER).is_file() else None), f"{source} {named}"
    for parent in [project, *project.parents]:
        for candidate in (parent / "code_factory", parent.parent / "code_factory"):
            if (candidate / SLICER).is_file():
                return candidate.resolve(), "sibling code_factory"
    return None, "no --factory-root, no SPEC_WORKBENCH_FACTORY_ROOT and no sibling code_factory"


def _unavailable(reason: str, **extra: Any) -> dict[str, Any]:
    return {"status": UNAVAILABLE, "reason": reason, "modules": {}, **extra}


def _project_paths(root: Path, factory_project: str) -> tuple[Path, Path]:
    structure = json.loads((root / STRUCTURE).read_text(encoding="utf-8"))
    project_root = root / structure["projects_dir"] / factory_project
    return project_root, project_root / structure["files"]["global_spec"]


def evidence(project: Path, factory_project: str | None, explicit_root: Path | None = None) -> dict[str, Any]:
    if factory_project is None:
        return {"status": NOT_APPLICABLE, "reason": "the case has no Factory target (90_factory_target.json)",
                "modules": {}}
    root, source = factory_root(project, explicit_root)
    if root is None:
        return _unavailable(f"no Factory checkout with {SLICER.as_posix()} ({source}); "
                            f"pass --factory-root or set {FACTORY_ROOT_ENV}")
    try:
        code_root, spec = _project_paths(root, factory_project)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        return _unavailable(f"the Factory structure cannot be read: {exc}", factory_root=str(root))
    if not spec.is_file():
        return _unavailable(f"the Factory project {factory_project} has no specification at {spec}",
                            factory_root=str(root))
    command = [sys.executable, "-m", "tools.slicer", "report", "--spec", str(spec), "--code-root", str(code_root),
               "--json"]
    try:
        result = subprocess.run(command, cwd=root, text=True, capture_output=True, check=False,
                                timeout=REPORT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return _unavailable(f"the Factory report did not finish in {REPORT_TIMEOUT_SECONDS}s",
                            factory_root=str(root))
    if result.returncode != 0:
        tail = (result.stderr or result.stdout).strip().splitlines()
        return _unavailable(f"the Factory report failed: {tail[-1] if tail else result.returncode}",
                            factory_root=str(root))
    try:
        report = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return _unavailable(f"the Factory report is not JSON: {exc}", factory_root=str(root))
    modules = report.get("modules") if isinstance(report, dict) else None
    if not isinstance(modules, dict) or any(not isinstance(m, dict) or "code_imports" not in m
                                            for m in modules.values()):
        return _unavailable("the Factory report has no code_imports (the Factory predates --code-root)",
                            factory_root=str(root))
    for name, module in modules.items():
        imports = module["code_imports"]
        if imports is not None and not (isinstance(imports, dict) and all(
                isinstance(p, str) and isinstance(s, list) and all(isinstance(x, str) for x in s)
                for p, s in imports.items())):
            return _unavailable(f"the Factory report's code_imports of {name} is not provider -> symbols",
                                factory_root=str(root))
    return {
        "status": AVAILABLE,
        "factory_root": str(root),
        "factory_project": factory_project,
        "code_root": str(code_root),
        # None: the module has no file in the product tree yet
        "modules": {name: m["code_imports"] for name, m in modules.items()},
    }
