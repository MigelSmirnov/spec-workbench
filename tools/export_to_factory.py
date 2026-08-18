#!/usr/bin/env python3
"""Export an accepted Workbench specification into a sibling Code Factory.

The export is intentionally blocked unless the Workbench and Factory copies of
SPEC_STANDARD.md are byte-identical and the Factory's canonical validator
accepts the source specification. Provenance is written beside generated working
artifacts, never into global_spec.json. A case may additionally declare
semantic-closed runtime acceptance tests for byte-exact handoff to the Factory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from factory_admission_workbench import check as check_factory_admission

HANDOFF_SCHEMA = "spec_workbench_handoff.v1"
SEMANTIC_EXPORT_SCHEMA = "spec_workbench_semantic_test_export.v1"
SEMANTIC_EXPORT_MANIFEST = "71_semantic_test_export.json"
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
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    value = result.stdout.strip()
    return value if result.returncode == 0 and value else None


def git_metadata(root: Path) -> dict[str, Any]:
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=root, text=True, capture_output=True, check=False)
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
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
        result = subprocess.run([sys.executable, str(validator), str(source), "--out", str(report_path), "--quiet"], text=True, capture_output=True, check=False)
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
        raise SystemExit(f"factory structure root points elsewhere: {configured_root} != {factory_root}")
    project_root = factory_root / structure["projects_dir"] / project
    return {
        "root": project_root,
        "canonical": project_root / structure["files"]["global_spec"],
        "working": project_root / structure["dirs"]["working"],
    }


def semantic_export_plan(source: Path, case: str | None) -> tuple[Path, dict[str, Any]] | None:
    if not case:
        return None
    case_root = source.parent
    manifest_path = case_root / SEMANTIC_EXPORT_MANIFEST
    if not manifest_path.is_file():
        return None
    manifest = load_json(manifest_path)
    if manifest.get("schema_version") != SEMANTIC_EXPORT_SCHEMA:
        raise SystemExit(f"unsupported semantic export manifest schema: {manifest_path}")
    if manifest.get("status") != "semantic_closed":
        raise SystemExit("semantic test export manifest exists but is not semantic_closed")
    flows = manifest.get("flows")
    if not isinstance(flows, list) or not flows:
        raise SystemExit("semantic test export manifest must declare at least one flow")
    seen: set[str] = set()
    for item in flows:
        relative = item.get("path") if isinstance(item, dict) else None
        if not isinstance(relative, str) or not relative:
            raise SystemExit("semantic test export flow has no path")
        source_test = (case_root / relative).resolve()
        if not source_test.is_relative_to(case_root.resolve()) or not source_test.is_file():
            raise SystemExit(f"semantic test source is missing or escapes case root: {relative}")
        if relative in seen:
            raise SystemExit(f"duplicate semantic test path in export manifest: {relative}")
        seen.add(relative)
    return manifest_path, manifest


def export_semantic_tests(plan: tuple[Path, dict[str, Any]] | None, project_root: Path, update_existing: bool) -> dict[str, Any] | None:
    if plan is None:
        return None
    manifest_path, manifest = plan
    case_root = manifest_path.parent
    target_root = project_root / manifest.get("target_dir", "tests/semantic")
    copied: list[dict[str, str]] = []
    for item in manifest["flows"]:
        relative = item["path"]
        source_test = (case_root / relative).resolve()
        source_dir = manifest.get("source_dir", "tests/semantic").rstrip("/") + "/"
        if not relative.startswith(source_dir):
            raise SystemExit(f"semantic test path is outside declared source_dir: {relative}")
        target_relative = relative[len(source_dir):]
        target_test = (target_root / target_relative).resolve()
        if not target_test.is_relative_to(project_root.resolve()):
            raise SystemExit(f"semantic test target escapes Factory project: {target_test}")
        source_sha = sha256_file(source_test)
        if target_test.exists():
            target_sha = sha256_file(target_test)
            if target_sha != source_sha and not update_existing:
                raise SystemExit(f"semantic test differs in Factory; pass --update-existing to replace: {target_test}")
        target_test.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_test, target_test)
        target_sha = sha256_file(target_test)
        if target_sha != source_sha:
            raise SystemExit(f"semantic test copy verification failed: {target_test}")
        copied.append({
            "flow_id": item["flow_id"],
            "source_path": str(source_test.relative_to(case_root)),
            "target_path": str(target_test.relative_to(project_root)),
            "sha256": source_sha,
        })
    return {
        "schema_version": manifest["schema_version"],
        "status": manifest["status"],
        "source_manifest_path": str(manifest_path.relative_to(case_root)),
        "runtime_binding": manifest.get("runtime_binding"),
        "factory_execution_verified": False,
        "files": copied,
    }


def stage9_lineage_manifest(
    *,
    project: str,
    source_sha: str,
    source_commit: str | None,
    standard_version: int,
    started_at: str,
    base_spec_path: Path,
    base_spec_sha_before: str | None,
    base_spec_sha_after: str,
    admission_path: Path,
    validation_path: Path,
    handoff_path: Path,
) -> dict[str, Any]:
    identity = source_commit[:16] if source_commit else source_sha[:16]
    return {
        "schema_version": 1,
        "project": project,
        "spec_editor_run_id": f"{project}-spec-workbench-{identity}",
        "spec_patch_id": f"{project}-spec-workbench-handoff-{source_sha[:16]}",
        "started_at": started_at,
        "finished_at": utc_now(),
        "status": "pass",
        "verdict": "PASS",
        "accepted": True,
        "producer": {
            "entrypoint": "tools/export_to_factory.py",
            "route": "spec_workbench_stage9",
            "mode": "external_canonical_handoff",
            "source": "spec_workbench",
            "argv": sys.argv,
        },
        "scope": {
            "module": "global",
            "allow_functions": [],
            "allow_notes": [],
            "forbid_contract_edits": False,
            "allowed_ops": ["accept_external_canonical_spec"],
        },
        "inputs": {
            "base_spec_path": str(base_spec_path),
            "base_spec_sha256_before": base_spec_sha_before,
            "source_spec_sha256": source_sha,
            "source_commit": source_commit,
            "standard_version": standard_version,
        },
        "outputs": {
            "base_spec_sha256_after": base_spec_sha_after,
            "factory_admission_path": str(admission_path),
            "factory_validation_path": str(validation_path),
            "spec_workbench_handoff_path": str(handoff_path),
        },
        "change_summary": {
            "diff_non_empty": True,
            "lineage_adoption": True,
            "changed_modules": ["global"],
            "changed_functions": [],
            "changed_notes": [],
            "changed_contracts": [],
            "changed_addresses": [],
            "applied_count": 1,
            "no_op_count": 0,
            "errors_count": 0,
            "removed_modules": [],
        },
        "findings": [],
    }


def main() -> int:
    export_started_at = utc_now()
    workbench_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--case", help="Case name under examples/")
    source_group.add_argument("--spec", type=Path, help="Explicit global_spec.json path")
    parser.add_argument("--project", required=True, help="Target project under Factory projects/")
    parser.add_argument("--factory-root", type=Path, default=workbench_root.parent / "code_factory", help="Sibling Code Factory checkout")
    parser.add_argument("--update-existing", action="store_true", help="Explicitly replace an existing project's canonical specification and differing semantic tests")
    parser.add_argument("--allow-dirty-source", action="store_true", help="Allow a non-reproducible export from a dirty Workbench checkout")
    parser.add_argument("--check", action="store_true", help="Run the Stage 9 admission gate without modifying Factory")
    args = parser.parse_args()

    if not PROJECT_RE.fullmatch(args.project):
        raise SystemExit("project must contain only letters, numbers, underscores, or hyphens")

    factory_root = args.factory_root.resolve()
    required = require_factory(factory_root)
    source = resolve_spec(workbench_root, args.case, args.spec)
    semantic_plan = semantic_export_plan(source, args.case)
    source_spec = load_json(source)
    if not isinstance(source_spec, dict):
        raise SystemExit("source specification must contain a JSON object")
    standard_version = source_spec.get("standard_version")
    if not isinstance(standard_version, int) or isinstance(standard_version, bool):
        raise SystemExit("source specification has no valid standard_version")

    workbench_git = git_metadata(workbench_root)
    admission = check_factory_admission(
        workbench_root=workbench_root,
        source=source,
        project=args.project,
        factory_root=factory_root,
        case_root=source.parent if args.case else None,
        update_existing=args.update_existing,
        allow_dirty_source=args.allow_dirty_source,
        source_git=workbench_git,
    )
    if args.check:
        print(json.dumps(admission, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if admission["ready"] else 1
    if not admission["ready"]:
        blockers = [
            item["summary"] for item in admission["checks"] if item["status"] == "BLOCK"
        ]
        raise SystemExit("Factory admission blocked: " + "; ".join(blockers))

    workbench_standard = workbench_root / "skills" / "spec-authoring" / "SPEC_STANDARD.md"
    workbench_standard_sha = sha256_file(workbench_standard)
    factory_standard_sha = sha256_file(required["standard"])
    if workbench_standard_sha != factory_standard_sha:
        raise SystemExit("SPEC_STANDARD mismatch: update or pin both repositories before exporting " f"(workbench={workbench_standard_sha}, factory={factory_standard_sha})")

    validation_report = admission["factory_validation"]
    if not isinstance(validation_report, dict):
        raise SystemExit("Factory admission did not return a canonical validation report")
    expected_validator_sha = canonical_spec_sha(source_spec)
    if validation_report.get("spec_sha") != expected_validator_sha:
        raise SystemExit("factory validation report is not bound to the source specification")

    structure = load_json(required["structure"])
    paths = project_paths(factory_root, structure, args.project)
    base_spec_sha_before = sha256_file(paths["canonical"]) if paths["canonical"].is_file() else None
    command = [sys.executable, str(required["bootstrap"]), "--project", args.project, "--spec", str(source)]
    if args.update_existing:
        command.extend(["--allow-existing", "--force-spec"])
    bootstrap = subprocess.run(command, cwd=factory_root, check=False)
    if bootstrap.returncode != 0:
        raise SystemExit(f"factory bootstrap failed with exit code {bootstrap.returncode}")

    if not paths["canonical"].is_file():
        raise SystemExit(f"factory did not create the canonical spec: {paths['canonical']}")
    source_sha = sha256_file(source)
    canonical_sha = sha256_file(paths["canonical"])
    canonical_spec = load_json(paths["canonical"])
    canonical_semantic_sha = canonical_spec_sha(canonical_spec)
    if canonical_spec != source_spec or canonical_semantic_sha != expected_validator_sha:
        raise SystemExit("canonical Factory specification differs semantically from the validated source")
    if not isinstance(canonical_spec, dict) or canonical_spec.get("standard_version") != standard_version:
        raise SystemExit("canonical Factory specification does not preserve source standard_version")

    semantic_handoff = export_semantic_tests(semantic_plan, paths["root"], args.update_existing)
    validation_path = paths["working"] / "spec_workbench_validation.json"
    write_json_atomic(validation_path, validation_report)
    admission_path = paths["working"] / "spec_workbench_factory_admission.json"
    exported_admission = dict(admission)
    exported_admission["status"] = "EXPORTED"
    exported_admission["ready"] = True
    write_json_atomic(admission_path, exported_admission)
    factory_git = git_metadata(factory_root)
    manifest = {
        "schema_version": HANDOFF_SCHEMA,
        "project": args.project,
        "exported_at": utc_now(),
        "source": {
            "case": args.case,
            "path": str(source.relative_to(workbench_root)) if source.is_relative_to(workbench_root) else str(source),
            "spec_sha256": source_sha,
            "canonical_spec_sha": expected_validator_sha,
            "standard_version": standard_version,
            "standard_sha256": workbench_standard_sha,
            **workbench_git,
        },
        "factory": {
            "canonical_spec_path": str(paths["canonical"].relative_to(factory_root)),
            "canonical_spec_sha256": canonical_sha,
            "canonical_spec_sha": canonical_semantic_sha,
            "standard_version": standard_version,
            "standard_sha256": factory_standard_sha,
            "commit": factory_git["commit"],
            "validation_report_path": str(validation_path.relative_to(factory_root)),
            "admission_report_path": str(admission_path.relative_to(factory_root)),
            "admission_status": exported_admission["status"],
            "validation_status": validation_report.get("status"),
            "validation_spec_sha": validation_report.get("spec_sha"),
            "semantic_tests": semantic_handoff,
        },
    }
    manifest_path = paths["working"] / "spec_workbench_handoff.json"
    lineage_path = paths["working"] / "spec_editor_manifest.json"
    manifest["factory"]["accepted_lineage_manifest_path"] = str(lineage_path.relative_to(factory_root))
    write_json_atomic(manifest_path, manifest)
    lineage = stage9_lineage_manifest(
        project=args.project,
        source_sha=source_sha,
        source_commit=workbench_git.get("commit"),
        standard_version=standard_version,
        started_at=export_started_at,
        base_spec_path=paths["canonical"],
        base_spec_sha_before=base_spec_sha_before,
        base_spec_sha_after=canonical_sha,
        admission_path=admission_path,
        validation_path=validation_path,
        handoff_path=manifest_path,
    )
    write_json_atomic(lineage_path, lineage)
    recorded_sha = lineage["outputs"]["base_spec_sha256_after"]
    if recorded_sha != sha256_file(paths["canonical"]):
        raise SystemExit("accepted Stage 9 lineage does not cover the canonical Factory spec")
    if lineage["inputs"].get("standard_version") != standard_version:
        raise SystemExit("accepted Stage 9 lineage does not cover the source standard_version")

    print(f"exported spec: {source}")
    print(f"canonical spec: {paths['canonical']}")
    if semantic_handoff:
        print(f"semantic tests: {len(semantic_handoff['files'])} copied byte-exact; Factory execution not verified")
    print(f"handoff manifest: {manifest_path}")
    print(f"accepted lineage: {lineage_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
