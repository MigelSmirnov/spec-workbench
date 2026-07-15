#!/usr/bin/env python3
"""Export an accepted Workbench specification into a sibling Code Factory.

The export is intentionally blocked unless the Workbench and Factory copies of
SPEC_STANDARD.md are byte-identical and the Factory's canonical validator
accepts the source specification.  Provenance is written beside generated
working artifacts, never into global_spec.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


HANDOFF_SCHEMA = "spec_workbench_handoff.v1"
PROJECT_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_spec_sha(spec: object) -> str:
    payload = json.dumps(spec, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git_value(root: Path, *args: str) -> str | None:
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def git_metadata(root: Path) -> dict[str, Any]:
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "commit": git_value(root, "rev-parse", "HEAD"),
        "branch": git_value(root, "branch", "--show-current"),
        "remote": git_value(root, "remote", "get-url", "origin"),
        "dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON: {path}: {exc}") from exc


def write_json_atomic(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def require_factory(factory_root: Path) -> dict[str, Path]:
    required = {
        "standard": factory_root / "SPEC_STANDARD.md",
        "validator": factory_root / "tools" / "validate_spec.py",
        "bootstrap": factory_root / "tools" / "bootstrap_project.py",
        "structure": factory_root / "project_index" / "structure.json",
    }
    missing = [str(path) for path in required.values() if not path.is_file()]
    if missing:
        raise SystemExit("factory checkout is incomplete; missing: " + ", ".join(missing))
    return required


def resolve_spec(workbench_root: Path, case: str | None, spec: Path | None) -> Path:
    if case:
        if not PROJECT_RE.fullmatch(case):
            raise SystemExit("case must contain only letters, numbers, underscores, or hyphens")
        source = workbench_root / "examples" / case / "global_spec.json"
    elif spec:
        source = spec if spec.is_absolute() else workbench_root / spec
    else:
        raise SystemExit("one of --case or --spec is required")
    source = source.resolve()
    if not source.is_file():
        raise SystemExit(f"source specification not found: {source}")
    if not source.is_relative_to(workbench_root.resolve()):
        raise SystemExit("source specification must be inside the Workbench checkout")
    return source


def run_factory_validator(validator: Path, source: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="spec-workbench-") as temp_dir:
        report_path = Path(temp_dir) / "validation.json"
        result = subprocess.run(
            [
                sys.executable,
                str(validator),
                str(source),
                "--out",
                str(report_path),
                "--quiet",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        report = load_json(report_path)
    if result.returncode not in (0, 2):
        errors = report.get("summary", {}).get("error", "unknown")
        raise SystemExit(f"factory validator rejected the source specification ({errors} errors)")
    return report


def project_paths(factory_root: Path, structure: dict[str, Any], project: str) -> dict[str, Path]:
    configured_root = Path(structure.get("root", factory_root))
    if configured_root.resolve() != factory_root.resolve():
        raise SystemExit(
            f"factory structure root points elsewhere: {configured_root} != {factory_root}"
        )
    project_root = factory_root / structure["projects_dir"] / project
    return {
        "root": project_root,
        "canonical": project_root / structure["files"]["global_spec"],
        "working": project_root / structure["dirs"]["working"],
    }


def main() -> int:
    workbench_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--case", help="Case name under examples/")
    source_group.add_argument("--spec", type=Path, help="Explicit global_spec.json path")
    parser.add_argument("--project", required=True, help="Target project under Factory projects/")
    parser.add_argument(
        "--factory-root",
        type=Path,
        default=workbench_root.parent / "code_factory",
        help="Sibling Code Factory checkout",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Explicitly replace an existing project's canonical specification",
    )
    parser.add_argument(
        "--allow-dirty-source",
        action="store_true",
        help="Allow a non-reproducible export from a dirty Workbench checkout",
    )
    args = parser.parse_args()

    if not PROJECT_RE.fullmatch(args.project):
        raise SystemExit("project must contain only letters, numbers, underscores, or hyphens")

    factory_root = args.factory_root.resolve()
    required = require_factory(factory_root)
    source = resolve_spec(workbench_root, args.case, args.spec)
    source_spec = load_json(source)
    if not isinstance(source_spec, dict):
        raise SystemExit("source specification must contain a JSON object")

    workbench_git = git_metadata(workbench_root)
    if workbench_git["dirty"] and not args.allow_dirty_source:
        raise SystemExit("Workbench checkout is dirty; commit the accepted source or pass --allow-dirty-source")

    workbench_standard = workbench_root / "skills" / "spec-authoring" / "SPEC_STANDARD.md"
    workbench_standard_sha = sha256_file(workbench_standard)
    factory_standard_sha = sha256_file(required["standard"])
    if workbench_standard_sha != factory_standard_sha:
        raise SystemExit(
            "SPEC_STANDARD mismatch: update or pin both repositories before exporting "
            f"(workbench={workbench_standard_sha}, factory={factory_standard_sha})"
        )

    validation_report = run_factory_validator(required["validator"], source)
    expected_validator_sha = canonical_spec_sha(source_spec)
    if validation_report.get("spec_sha") != expected_validator_sha:
        raise SystemExit("factory validation report is not bound to the source specification")

    structure = load_json(required["structure"])
    paths = project_paths(factory_root, structure, args.project)
    command = [
        sys.executable,
        str(required["bootstrap"]),
        "--project",
        args.project,
        "--spec",
        str(source),
    ]
    if args.update_existing:
        command.extend(["--allow-existing", "--force-spec"])
    bootstrap = subprocess.run(command, cwd=factory_root, check=False)
    if bootstrap.returncode != 0:
        raise SystemExit(f"factory bootstrap failed with exit code {bootstrap.returncode}")

    if not paths["canonical"].is_file():
        raise SystemExit(f"factory did not create the canonical spec: {paths['canonical']}")
    source_sha = sha256_file(source)
    canonical_sha = sha256_file(paths["canonical"])
    if source_sha != canonical_sha:
        raise SystemExit("canonical Factory specification differs from the validated source")

    validation_path = paths["working"] / "spec_workbench_validation.json"
    write_json_atomic(validation_path, validation_report)
    factory_git = git_metadata(factory_root)
    manifest = {
        "schema_version": HANDOFF_SCHEMA,
        "project": args.project,
        "exported_at": utc_now(),
        "source": {
            "case": args.case,
            "path": str(source.relative_to(workbench_root)) if source.is_relative_to(workbench_root) else str(source),
            "spec_sha256": source_sha,
            "standard_sha256": workbench_standard_sha,
            **workbench_git,
        },
        "factory": {
            "canonical_spec_path": str(paths["canonical"].relative_to(factory_root)),
            "canonical_spec_sha256": canonical_sha,
            "standard_sha256": factory_standard_sha,
            "commit": factory_git["commit"],
            "validation_report_path": str(validation_path.relative_to(factory_root)),
            "validation_status": validation_report.get("status"),
            "validation_spec_sha": validation_report.get("spec_sha"),
        },
    }
    manifest_path = paths["working"] / "spec_workbench_handoff.json"
    write_json_atomic(manifest_path, manifest)

    print(f"exported spec: {source}")
    print(f"canonical spec: {paths['canonical']}")
    print(f"handoff manifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
