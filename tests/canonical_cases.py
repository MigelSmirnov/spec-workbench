"""Resolve a case at its canonical ref for tests that assert on the canonical case.

PROJECT_INDEX.json names the ref where each case is authored. The copy under
``examples/`` on another ref is a snapshot, not the case; a test that asserts on
the case must read the canonical one or say truthfully that it is absent.

Resolution order:

1. ``SPEC_WORKBENCH_CANONICAL_CASES`` — a directory holding ``examples/<case>``;
2. ``canonical-cases/examples/<case>`` inside the checkout (CI fetches it by
   canonical_ref, see .github/workflows/spec-workbench-ci.yml);
3. ``examples/<case>`` of this checkout when the checked-out branch is the
   canonical ref itself;
4. otherwise the test is skipped with the reason.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def canonical_ref(case_id: str) -> str:
    index = json.loads((ROOT / "PROJECT_INDEX.json").read_text(encoding="utf-8"))
    for project in index.get("projects", []) + index.get("reference_cases", []):
        if project.get("id") == case_id:
            return str(project["canonical_ref"])
    raise KeyError(f"{case_id} is not in PROJECT_INDEX.json")


def _current_branch() -> str | None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "branch", "--show-current"], capture_output=True, text=True
    )
    return result.stdout.strip() or None if result.returncode == 0 else None


def find_canonical_case(case_id: str) -> Path | None:
    override = os.environ.get("SPEC_WORKBENCH_CANONICAL_CASES")
    candidates = []
    if override:
        candidates.append(Path(override) / "examples" / case_id)
    candidates.append(ROOT / "canonical-cases" / "examples" / case_id)
    for candidate in candidates:
        if (candidate / "global_spec.json").is_file() or (candidate / "30_modules.md").is_file():
            return candidate
    if _current_branch() == canonical_ref(case_id):
        local = ROOT / "examples" / case_id
        if local.is_dir():
            return local
    return None


def canonical_case(case_id: str) -> Path:
    """The canonical case directory, or a pytest skip naming what is missing."""
    found = find_canonical_case(case_id)
    if found is None:
        pytest.skip(
            f"canonical case {case_id} ({canonical_ref(case_id)}) is not checked out; "
            "CI fetches it into canonical-cases/, locally set SPEC_WORKBENCH_CANONICAL_CASES"
        )
    return found
