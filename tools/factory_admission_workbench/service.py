from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from assembly_workbench import verify as verify_assembly
from spec_projection_workbench import verify as verify_projection
from spec_projection_workbench.model import SpecProjectionError
from module_review_workbench import build_slice
from external_contract_workbench import coverage as external_contract_coverage
from notes_workbench.language import signature_parameters
from spec_language_workbench import SpecLanguageError, verify_payload as verify_language_payload

from factory_admission_workbench.model import (
    CHECK_BLOCK,
    CHECK_NOT_APPLICABLE,
    CHECK_PASS,
    CHECK_WARNING,
    REPORT_SCHEMA,
    AdmissionCheck,
)


SEMANTIC_EXPORT_SCHEMA = "spec_workbench_semantic_test_export.v1"
SEMANTIC_EXPORT_MANIFEST = "71_semantic_test_export.json"
REVIEW_LEDGER = "81_module_review_status.json"
FACTORY_TARGET_SCHEMA = "spec_workbench_factory_target.v1"
FACTORY_TARGET_MANIFEST = "90_factory_target.json"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_spec_sha(spec: object) -> str:
    payload = json.dumps(spec, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _git_value(root: Path, *args: str) -> str | None:
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
        "commit": _git_value(root, "rev-parse", "HEAD"),
        "branch": _git_value(root, "branch", "--show-current"),
        "remote": _git_value(root, "remote", "get-url", "origin"),
        "dirty": bool(dirty.stdout.strip()) if dirty.returncode == 0 else None,
    }


def _source_clean_check(metadata: dict[str, Any], allow_dirty_source: bool) -> AdmissionCheck:
    if metadata.get("dirty") is True:
        if allow_dirty_source:
            return AdmissionCheck(
                "FA001",
                CHECK_WARNING,
                "Dirty Workbench source was explicitly allowed; handoff will be non-reproducible.",
                metadata,
            )
        return AdmissionCheck(
            "FA001",
            CHECK_BLOCK,
            "Workbench checkout is dirty; commit the accepted source before handoff.",
            metadata,
        )
    if metadata.get("dirty") is None:
        return AdmissionCheck(
            "FA001",
            CHECK_WARNING,
            "Workbench git cleanliness could not be determined.",
            metadata,
        )
    return AdmissionCheck(
        "FA001", CHECK_PASS, "Workbench source is committed and clean.", metadata
    )


def _target_identity_check(case_root: Path | None, project: str) -> AdmissionCheck:
    if case_root is None:
        return AdmissionCheck(
            "FA014",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no case-to-Factory target declaration.",
            {"factory_project": project},
        )
    manifest_path = case_root / FACTORY_TARGET_MANIFEST
    if not manifest_path.is_file():
        return AdmissionCheck(
            "FA014",
            CHECK_WARNING,
            "Case has no pinned Factory target; the CLI project name is not independently verified.",
            {
                "case": case_root.name,
                "factory_project": project,
                "missing": str(manifest_path),
            },
        )
    manifest = _load_json(manifest_path)
    expected_case = manifest.get("case") if isinstance(manifest, dict) else None
    expected_project = manifest.get("factory_project") if isinstance(manifest, dict) else None
    valid = (
        isinstance(manifest, dict)
        and manifest.get("schema_version") == FACTORY_TARGET_SCHEMA
        and expected_case == case_root.name
        and expected_project == project
    )
    return AdmissionCheck(
        "FA014",
        CHECK_PASS if valid else CHECK_BLOCK,
        "Workbench case is pinned to the requested Factory project."
        if valid
        else "Workbench case and requested Factory project do not match the pinned target.",
        {
            "path": str(manifest_path),
            "schema_version": manifest.get("schema_version") if isinstance(manifest, dict) else None,
            "expected_schema_version": FACTORY_TARGET_SCHEMA,
            "case": case_root.name,
            "declared_case": expected_case,
            "requested_factory_project": project,
            "declared_factory_project": expected_project,
        },
    )


def _review_check(case_root: Path | None) -> AdmissionCheck:
    if case_root is None:
        return AdmissionCheck(
            "FA002",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no case-level Stage 8.1 ledger.",
            {},
        )
    ledger_path = case_root / REVIEW_LEDGER
    if not ledger_path.is_file():
        return AdmissionCheck(
            "FA002",
            CHECK_BLOCK,
            "Case has no Stage 8.1 module-review ledger; semantic implementation readiness is unproven.",
            {"path": str(ledger_path)},
        )
    ledger = _load_json(ledger_path)
    summary = ledger.get("summary", {})
    modules = ledger.get("modules", [])
    closed = (
        ledger.get("status") == "closed"
        and summary.get("reviewed") == summary.get("module_count")
        and summary.get("passed") == summary.get("module_count")
        and summary.get("ambiguities") == 0
        and summary.get("pending") == 0
        and summary.get("stale") == 0
    )
    changed: list[str] = []
    if closed:
        for item in modules:
            packet = build_slice(case_root, item["module"])
            rendered = json.dumps(
                packet, indent=2, ensure_ascii=False, sort_keys=True
            ) + "\n"
            actual = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
            if actual != item.get("slice_sha256"):
                changed.append(item["module"])
    if not closed or changed:
        return AdmissionCheck(
            "FA002",
            CHECK_BLOCK,
            "Stage 8.1 is not closed against the current assembled module slices.",
            {"path": str(ledger_path), "summary": summary, "changed_modules": changed},
        )
    return AdmissionCheck(
        "FA002",
        CHECK_PASS,
        "Stage 8.1 is closed and every recorded module slice hash is current.",
        {"path": str(ledger_path), "summary": summary},
    )


def _runtime_persistence_check(source_spec: object, case_root: Path | None) -> AdmissionCheck:
    """Require a closed persistence backend when the spec declares master state.

    ``persistence.<Model>.class = master`` is structured evidence that the
    application owns durable state.  Treating the backend as optional in that
    situation leaves repository, unit-of-work, atomicity, and restart behavior
    for the generator to invent.  Stage 9 must stop before that can happen.

    Explicit ``--spec`` admission remains outside the case authoring sequence;
    it has no Stage 8.1/runtime-closure evidence to validate here.
    """
    if case_root is None:
        return AdmissionCheck(
            "FA013",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no case-level runtime-closure evidence.",
            {},
        )
    spec = source_spec if isinstance(source_spec, dict) else {}
    persistence = spec.get("persistence")
    persistent_masters = sorted(
        name
        for name, declaration in (persistence.items() if isinstance(persistence, dict) else [])
        if isinstance(name, str)
        and isinstance(declaration, dict)
        and declaration.get("class") == "master"
    )
    if not persistent_masters:
        return AdmissionCheck(
            "FA013",
            CHECK_NOT_APPLICABLE,
            "Case declares no master persistence requiring a backend closure.",
            {"persistent_masters": []},
        )
    rules = spec.get("rules")
    backend = rules.get("persistence_backend") if isinstance(rules, dict) else None
    if not isinstance(backend, dict):
        return AdmissionCheck(
            "FA013",
            CHECK_BLOCK,
            "Master persistence is declared without rules.persistence_backend; runtime implementation decisions remain open.",
            {
                "persistent_masters": persistent_masters,
                "missing": "rules.persistence_backend",
                "revision_entrypoint": "Stage 8.1 module review",
                "repair_policy": "return each open decision to its earliest owning design state",
            },
        )
    tables = backend.get("tables")
    repositories = backend.get("repositories")
    if not isinstance(tables, list) or not tables or not isinstance(repositories, list) or not repositories:
        return AdmissionCheck(
            "FA013",
            CHECK_BLOCK,
            "Master persistence has a backend marker but no concrete table/repository lowering.",
            {
                "persistent_masters": persistent_masters,
                "tables": len(tables) if isinstance(tables, list) else None,
                "repositories": len(repositories) if isinstance(repositories, list) else None,
                "revision_entrypoint": "Stage 8.1 module review",
                "repair_policy": "complete persistence projection and repository ownership before generation",
            },
        )
    closure_path = case_root / "70_persistence_closure.json"
    if not closure_path.is_file():
        return AdmissionCheck(
            "FA013",
            CHECK_BLOCK,
            "Structured persistence backend has no post-contract authoring closure.",
            {
                "persistent_masters": persistent_masters,
                "missing": str(closure_path),
                "revision_entrypoint": "Stage 8.1 module review",
            },
        )
    closure = _load_json(closure_path)
    if closure.get("status") != "closed":
        return AdmissionCheck(
            "FA013",
            CHECK_BLOCK,
            "Persistence backend authoring remains open and is not eligible for Factory generation.",
            {
                "persistent_masters": persistent_masters,
                "path": str(closure_path),
                "closure_status": closure.get("status"),
                "tables": len(tables),
                "repositories": len(repositories),
                "revision_entrypoint": "Stage 8.1 module review",
            },
        )
    return AdmissionCheck(
        "FA013",
        CHECK_PASS,
        "Master persistence has a closed structured persistence-backend authoring handoff.",
        {
            "persistent_masters": persistent_masters,
            "backend_kind": backend.get("kind"),
            "backend_schema_version": backend.get("schema_version"),
            "tables": len(tables),
            "repositories": len(repositories),
        },
    )


def _assembly_check(case_root: Path | None) -> AdmissionCheck:
    if case_root is None:
        return AdmissionCheck(
            "FA003",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no Workbench assembly project.",
            {},
        )
    report = verify_assembly(case_root)
    return AdmissionCheck(
        "FA003",
        CHECK_PASS if report["ready"] else CHECK_BLOCK,
        "Workbench assembly is ready." if report["ready"] else "Workbench assembly is blocked.",
        report["summary"],
    )


def _external_contract_check(case_root: Path | None) -> AdmissionCheck:
    if case_root is None:
        return AdmissionCheck(
            "FA011",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no Workbench external-contract evidence.",
            {},
        )
    report = external_contract_coverage(case_root)
    if report["status"] == "not_applicable":
        return AdmissionCheck(
            "FA011",
            CHECK_NOT_APPLICABLE,
            "Case declares no verified external-contract evidence.",
            {"manifest": report["manifest"], "summary": report["summary"]},
        )
    ready = bool(report["summary"]["handoff_ready"])
    evidence = {
        "manifest": report["manifest"],
        "manifest_sha256": report["manifest_sha256"],
        "summary": report["summary"],
        "contracts": [
            {
                "id": record["id"],
                "status": record["status"],
                "verified_by": record["verified_by"],
                "verified_at": record["verified_at"],
                "artifact": record["evidence"]["artifact"],
                "artifact_sha256": record["evidence"]["sha256"],
                "run_id": record["evidence"]["run_id"],
            }
            for record in report["contracts"]
        ],
        "findings": report["findings"],
    }
    return AdmissionCheck(
        "FA011",
        CHECK_PASS if ready else CHECK_BLOCK,
        "External-contract evidence is closed and content-addressed."
        if ready else "External-contract evidence is invalid or stale.",
        evidence,
    )


def _closure_gaps_check(case_root: Path | None) -> AdmissionCheck:
    if case_root is None:
        return AdmissionCheck(
            "FA012",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no Workbench case for closure-gap fuses.",
            {},
        )
    from design_closure_gaps import run as closure_gaps_run

    report = closure_gaps_run(case_root)
    waivers_path = case_root / "closure_gap_waivers.json"
    waivers: list[dict[str, Any]] = []
    if waivers_path.is_file():
        loaded = _load_json(waivers_path)
        if isinstance(loaded, dict):
            waivers = [w for w in loaded.get("waivers", []) if isinstance(w, dict)]

    def waived(finding: dict[str, Any]) -> bool:
        for waiver in waivers:
            keys = {k: v for k, v in waiver.items() if k not in {"reason", "decided"}}
            if keys and all(finding.get(k) == v for k, v in keys.items()):
                return bool(waiver.get("reason"))
        return False

    open_findings = [f for f in report["findings"] if not waived(f)]
    waived_count = len(report["findings"]) - len(open_findings)
    evidence = {
        "summary": report["summary"],
        "open_findings": open_findings,
        "waived": waived_count,
        "waivers_file": str(waivers_path) if waivers else None,
    }
    if open_findings:
        return AdmissionCheck(
            "FA012",
            CHECK_BLOCK,
            f"Closure-gap fuses report {len(open_findings)} unwaived finding(s): "
            "the specification reads, returns, or closes in prose what nothing produces.",
            evidence,
        )
    return AdmissionCheck(
        "FA012",
        CHECK_PASS,
        "Closure-gap fuses are clean" + (f" ({waived_count} waived with reasons)." if waived_count else "."),
        evidence,
    )


def _projection_drift_check(case_root: Path | None) -> AdmissionCheck:
    """Require global_spec.json to equal its deterministic projection.

    The stage handoffs are the authoring source of truth and
    ``design_spec_projection --apply`` is the only sanctioned writer of
    ``global_spec.json``.  A hand edit that drifts from the projection ships a
    value no gate ever compared: the notes gate resolves address existence,
    the Stage 6 lint pairs placements with values, but nothing else proves the
    exported literal equals the authored one.
    """
    if case_root is None:
        return AdmissionCheck(
            "FA016",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no Workbench projection sources.",
            {},
        )
    try:
        report = verify_projection(case_root)
    except SpecProjectionError as error:
        return AdmissionCheck(
            "FA016",
            CHECK_BLOCK,
            f"Spec projection cannot be built: {error}",
            {"error": str(error)},
        )
    summary = report.get("summary") if isinstance(report, dict) else None
    summary = summary if isinstance(summary, dict) else {}
    in_sync = report.get("in_sync") is True if isinstance(report, dict) else False
    ready = report.get("ready") is True if isinstance(report, dict) else False
    if not ready:
        return AdmissionCheck(
            "FA016",
            CHECK_BLOCK,
            "Spec projection sources are not ready; close the authoring handoffs first.",
            {"summary": summary},
        )
    if not in_sync:
        return AdmissionCheck(
            "FA016",
            CHECK_BLOCK,
            (
                "global_spec.json drifts from its deterministic projection; "
                "author the stage files and run design_spec_projection --apply "
                "instead of editing global_spec.json by hand."
            ),
            {"summary": summary},
        )
    return AdmissionCheck(
        "FA016",
        CHECK_PASS,
        "global_spec.json equals its deterministic projection.",
        {"summary": summary},
    )


def _standard_check(workbench_root: Path, factory_root: Path) -> AdmissionCheck:
    workbench = workbench_root / "skills/spec-authoring/SPEC_STANDARD.md"
    factory = factory_root / "SPEC_STANDARD.md"
    if not workbench.is_file() or not factory.is_file():
        return AdmissionCheck(
            "FA004",
            CHECK_BLOCK,
            "SPEC_STANDARD.md is missing from Workbench or Factory.",
            {"workbench": str(workbench), "factory": str(factory)},
        )
    workbench_sha = _sha256_file(workbench)
    factory_sha = _sha256_file(factory)
    status = CHECK_PASS if workbench_sha == factory_sha else CHECK_BLOCK
    summary = (
        "Workbench and Factory SPEC_STANDARD.md are byte-identical."
        if status == CHECK_PASS
        else f"SPEC_STANDARD mismatch: workbench={workbench_sha}, factory={factory_sha}"
    )
    return AdmissionCheck(
        "FA004",
        status,
        summary,
        {"workbench_sha256": workbench_sha, "factory_sha256": factory_sha},
    )


def _language_check(source: Path) -> AdmissionCheck:
    try:
        report = verify_language_payload(_load_json(source), project_root=source.stem)
    except (OSError, json.JSONDecodeError, SpecLanguageError) as exc:
        return AdmissionCheck(
            "FA009",
            CHECK_BLOCK,
            "Source specification language revision cannot be verified.",
            {"path": str(source), "error": str(exc)},
        )
    return AdmissionCheck(
        "FA009",
        CHECK_PASS if report["ready"] else CHECK_BLOCK,
        "Source specification declares the supported SPEC_STANDARD revision."
        if report["ready"]
        else "Source specification does not declare the supported SPEC_STANDARD revision.",
        {
            "path": str(source),
            "standard_version": report["standard_version"],
            "supported_standard_version": report["supported_standard_version"],
            "findings": report["findings"],
        },
    )


def _annotation_mentions(annotation: str, type_name: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(type_name)}(?![A-Za-z0-9_])", annotation) is not None


def _implementation_obligations_check(source: Path) -> AdmissionCheck:
    """Require an explicit disposition for every interface used as a dependency.

    A local implementation is accepted only when its concrete class contracts
    cover the complete interface method surface.  This deliberately uses only
    structured spec cells; class names and prose notes are not evidence.
    """
    spec = _load_json(source)
    contracts = spec.get("contracts", {}) if isinstance(spec, dict) else None
    models = spec.get("models", {}) if isinstance(spec, dict) else None
    obligations = spec.get("implementation_obligations") if isinstance(spec, dict) else None
    if not isinstance(contracts, dict) or not isinstance(models, dict):
        return AdmissionCheck(
            "FA010",
            CHECK_BLOCK,
            "Implementation obligations cannot be checked on malformed contracts/models.",
            {"path": str(source)},
        )

    interfaces = {
        name
        for name, declaration in models.items()
        if isinstance(name, str)
        and isinstance(declaration, dict)
        and declaration.get("kind") == "interface"
    }
    dependency_uses: dict[str, list[str]] = {name: [] for name in interfaces}
    for owner, signature in contracts.items():
        if not isinstance(owner, str) or not isinstance(signature, str):
            continue
        owner_class = owner.split(".", 1)[0] if "." in owner else None
        for _parameter, annotation in signature_parameters(signature):
            for interface in interfaces:
                if owner_class != interface and _annotation_mentions(annotation, interface):
                    dependency_uses[interface].append(owner)
    dependency_uses = {name: sorted(set(uses)) for name, uses in dependency_uses.items() if uses}
    if not dependency_uses:
        return AdmissionCheck(
            "FA010",
            CHECK_NOT_APPLICABLE,
            "No interface-typed dependency parameters require an implementation disposition.",
            {"interfaces": sorted(interfaces)},
        )

    findings: list[dict[str, Any]] = []
    if not isinstance(obligations, dict):
        obligations = {}
    unknown = sorted(set(obligations) - interfaces)
    for interface in unknown:
        findings.append({
            "code": "unknown_interface_obligation",
            "interface": interface,
        })

    interface_methods: dict[str, dict[str, str]] = {}
    for interface in interfaces:
        prefix = interface + "."
        interface_methods[interface] = {
            name[len(prefix):]: signature
            for name, signature in contracts.items()
            if isinstance(name, str)
            and name.startswith(prefix)
            and isinstance(signature, str)
        }

    module_functions = spec.get("module_functions") or {}
    declared_classes = {
        symbol
        for symbols in module_functions.values()
        if isinstance(symbols, list)
        for symbol in symbols
        if isinstance(symbol, str)
        and any(name.startswith(symbol + ".") for name in contracts)
    } if isinstance(module_functions, dict) else set()

    for interface, uses in sorted(dependency_uses.items()):
        row = obligations.get(interface)
        if not isinstance(row, dict):
            findings.append({
                "code": "missing_implementation_disposition",
                "interface": interface,
                "used_by": uses,
            })
            continue
        disposition = row.get("disposition")
        implementations = row.get("implementations", [])
        if disposition not in {"local", "policy", "external"}:
            findings.append({
                "code": "invalid_implementation_disposition",
                "interface": interface,
                "disposition": disposition,
            })
            continue
        if disposition == "external":
            if implementations not in (None, []):
                findings.append({
                    "code": "external_disposition_has_local_classes",
                    "interface": interface,
                })
            continue
        if not isinstance(implementations, list) or not implementations:
            findings.append({
                "code": "local_disposition_has_no_classes",
                "interface": interface,
            })
            continue
        for concrete in implementations:
            if not isinstance(concrete, str) or concrete not in declared_classes or concrete in interfaces:
                findings.append({
                    "code": "unknown_concrete_implementation",
                    "interface": interface,
                    "concrete": concrete,
                })
                continue
            for method, expected in sorted(interface_methods[interface].items()):
                concrete_contract = f"{concrete}.{method}"
                actual = contracts.get(concrete_contract)
                if actual is None:
                    findings.append({
                        "code": "missing_concrete_method_contract",
                        "interface": interface,
                        "concrete": concrete,
                        "method": method,
                        "expected_contract": expected,
                    })
                elif actual != expected:
                    findings.append({
                        "code": "incompatible_concrete_method_contract",
                        "interface": interface,
                        "concrete": concrete,
                        "method": method,
                        "expected_contract": expected,
                        "actual_contract": actual,
                    })

    return AdmissionCheck(
        "FA010",
        CHECK_BLOCK if findings else CHECK_PASS,
        "Concrete implementation obligations cover every interface-typed dependency."
        if not findings
        else "Interface-typed dependencies have incomplete concrete implementation obligations.",
        {
            "path": str(source),
            "dependency_uses": dependency_uses,
            "findings": findings,
        },
    )


def _factory_validation_check(factory_root: Path, source: Path) -> tuple[AdmissionCheck, dict[str, Any] | None]:
    validator = factory_root / "tools/validate_spec.py"
    if not validator.is_file():
        return AdmissionCheck(
            "FA005",
            CHECK_BLOCK,
            "Factory canonical validator is missing.",
            {"path": str(validator)},
        ), None
    with tempfile.TemporaryDirectory(prefix="spec-workbench-admission-") as temp_dir:
        report_path = Path(temp_dir) / "validation.json"
        result = subprocess.run(
            [sys.executable, str(validator), str(source), "--out", str(report_path), "--quiet"],
            text=True,
            capture_output=True,
            check=False,
        )
        if not report_path.is_file():
            return AdmissionCheck(
                "FA005",
                CHECK_BLOCK,
                "Factory validator did not produce a bound report.",
                {"returncode": result.returncode, "stderr": result.stderr.strip()},
            ), None
        report = _load_json(report_path)
    source_spec = _load_json(source)
    expected_sha = _canonical_spec_sha(source_spec)
    ready = (
        report.get("status") == "PASS"
        and report.get("summary", {}).get("error") == 0
        and report.get("spec_sha") == expected_sha
        and result.returncode in (0, 2)
    )
    return AdmissionCheck(
        "FA005",
        CHECK_PASS if ready else CHECK_BLOCK,
        "Factory canonical validator accepts the source specification."
        if ready
        else "Factory canonical validator rejects the source specification.",
        {
            "returncode": result.returncode,
            "status": report.get("status"),
            "summary": report.get("summary"),
            "spec_sha": report.get("spec_sha"),
            "expected_spec_sha": expected_sha,
            "findings": report.get("findings", []),
        },
    ), report


def _factory_inspector_check(
    factory_root: Path, project: str, source: Path
) -> tuple[AdmissionCheck, dict[str, Any] | None]:
    runner = factory_root / "tools/run_spec_inspector_preflight.py"
    if not runner.is_file():
        return AdmissionCheck(
            "FA015",
            CHECK_BLOCK,
            "Factory Spec Inspector preflight is missing.",
            {"path": str(runner)},
        ), None
    with tempfile.TemporaryDirectory(prefix="spec-workbench-inspector-") as temp_dir:
        report_path = Path(temp_dir) / "spec_inspector_report.json"
        result = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--project",
                project,
                "--spec",
                str(source),
                "--out",
                str(report_path),
            ],
            cwd=factory_root,
            text=True,
            capture_output=True,
            check=False,
        )
        if not report_path.is_file():
            return AdmissionCheck(
                "FA015",
                CHECK_BLOCK,
                "Factory Spec Inspector did not produce a bound report.",
                {
                    "returncode": result.returncode,
                    "stdout": result.stdout.strip(),
                    "stderr": result.stderr.strip(),
                },
            ), None
        report = _load_json(report_path)
    source_sha = "sha256:" + _sha256_file(source)
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    ready = (
        report.get("status") == "PASS"
        and summary.get("BLOCK") == 0
        and report.get("spec_sha") == source_sha
        and result.returncode == 0
    )
    return AdmissionCheck(
        "FA015",
        CHECK_PASS if ready else CHECK_BLOCK,
        "Factory Spec Inspector accepts the source specification."
        if ready
        else "Factory Spec Inspector rejects the source specification.",
        {
            "returncode": result.returncode,
            "status": report.get("status"),
            "summary": summary,
            "spec_sha": report.get("spec_sha"),
            "expected_spec_sha": source_sha,
            "findings": report.get("findings", []),
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        },
    ), report


def _semantic_check(case_root: Path | None) -> AdmissionCheck:
    if case_root is None:
        return AdmissionCheck(
            "FA006",
            CHECK_NOT_APPLICABLE,
            "Explicit --spec admission has no semantic handoff manifest.",
            {},
        )
    manifest_path = case_root / SEMANTIC_EXPORT_MANIFEST
    if not manifest_path.is_file():
        return AdmissionCheck(
            "FA006",
            CHECK_NOT_APPLICABLE,
            "Case declares no semantic runtime-test handoff.",
            {"path": str(manifest_path)},
        )
    manifest = _load_json(manifest_path)
    errors: list[str] = []
    files: list[dict[str, str]] = []
    if manifest.get("schema_version") != SEMANTIC_EXPORT_SCHEMA:
        errors.append("unsupported schema_version")
    if manifest.get("status") != "semantic_closed":
        errors.append("status is not semantic_closed")
    flows = manifest.get("flows")
    if not isinstance(flows, list) or not flows:
        errors.append("flows is empty")
    else:
        for item in flows:
            relative = item.get("path") if isinstance(item, dict) else None
            if not isinstance(relative, str):
                errors.append("flow path is missing")
                continue
            path = (case_root / relative).resolve()
            if not path.is_relative_to(case_root.resolve()) or not path.is_file():
                errors.append(f"missing or escaping semantic test: {relative}")
                continue
            files.append({"path": relative, "sha256": _sha256_file(path)})
    return AdmissionCheck(
        "FA006",
        CHECK_BLOCK if errors else CHECK_PASS,
        "Semantic runtime-test handoff is closed and byte-addressable."
        if not errors
        else "Semantic runtime-test handoff is invalid.",
        {"path": str(manifest_path), "errors": errors, "files": files},
    )


def _target_check(factory_root: Path, project: str, source: Path, update_existing: bool) -> AdmissionCheck:
    canonical = factory_root / "projects" / project / "specs/base/global_spec.json"
    lineage_path = factory_root / "projects" / project / "specs/working/spec_editor_manifest.json"
    source_sha = _sha256_file(source)
    source_spec = _load_json(source)
    source_spec_sha = _canonical_spec_sha(source_spec)
    source_standard_version = source_spec.get("standard_version") if isinstance(source_spec, dict) else None
    if not canonical.is_file():
        return AdmissionCheck(
            "FA007",
            CHECK_PASS,
            "Factory target is new and may be created.",
            {
                "action": "create",
                "canonical_path": str(canonical),
                "source_sha256": source_sha,
                "source_spec_sha": source_spec_sha,
                "standard_version": source_standard_version,
            },
        )
    canonical_sha = _sha256_file(canonical)
    canonical_spec = _load_json(canonical)
    canonical_spec_sha = _canonical_spec_sha(canonical_spec)
    canonical_standard_version = canonical_spec.get("standard_version") if isinstance(canonical_spec, dict) else None
    if canonical_spec_sha == source_spec_sha:
        lineage = _load_json(lineage_path) if lineage_path.is_file() else {}
        lineage_inputs = lineage.get("inputs") or {}
        lineage_fresh = (
            lineage.get("accepted") is True
            and lineage.get("status") == "pass"
            and lineage.get("verdict") == "PASS"
            and (lineage.get("outputs") or {}).get("base_spec_sha256_after") == canonical_sha
            and lineage_inputs.get("standard_version") == source_standard_version
            and canonical_standard_version == source_standard_version
            and bool((lineage.get("change_summary") or {}).get("changed_modules"))
        )
        return AdmissionCheck(
            "FA007",
            CHECK_PASS,
            "Factory already contains the exact source specification and accepted version-bound lineage."
            if lineage_fresh
            else "Factory contains the exact source specification; export will adopt it into version-bound accepted lineage.",
            {
                "action": "noop" if lineage_fresh else "accept_lineage",
                "canonical_path": str(canonical),
                "lineage_path": str(lineage_path),
                "lineage_fresh": lineage_fresh,
                "source_sha256": source_sha,
                "canonical_sha256": canonical_sha,
                "source_spec_sha": source_spec_sha,
                "canonical_spec_sha": canonical_spec_sha,
                "source_standard_version": source_standard_version,
                "canonical_standard_version": canonical_standard_version,
                "lineage_standard_version": lineage_inputs.get("standard_version"),
            },
        )
    if not update_existing:
        return AdmissionCheck(
            "FA007",
            CHECK_BLOCK,
            "Factory target has a different canonical spec; explicit --update-existing is required.",
            {
                "action": "blocked_update",
                "canonical_path": str(canonical),
                "source_sha256": source_sha,
                "canonical_sha256": canonical_sha,
                "source_spec_sha": source_spec_sha,
                "canonical_spec_sha": canonical_spec_sha,
                "source_standard_version": source_standard_version,
                "canonical_standard_version": canonical_standard_version,
            },
        )
    return AdmissionCheck(
        "FA007",
        CHECK_PASS,
        "Explicit replacement of the existing Factory canonical spec is authorized.",
        {
            "action": "update",
            "canonical_path": str(canonical),
            "source_sha256": source_sha,
            "canonical_sha256": canonical_sha,
            "source_spec_sha": source_spec_sha,
            "canonical_spec_sha": canonical_spec_sha,
            "source_standard_version": source_standard_version,
            "canonical_standard_version": canonical_standard_version,
        },
    )


def _factory_toolchain_check(factory_root: Path) -> AdmissionCheck:
    metadata = git_metadata(factory_root)
    required = [
        factory_root / "SPEC_STANDARD.md",
        factory_root / "tools/validate_spec.py",
        factory_root / "tools/run_spec_inspector_preflight.py",
        factory_root / "tools/bootstrap_project.py",
        factory_root / "project_index/structure.json",
    ]
    fingerprints = {
        str(path.relative_to(factory_root)): _sha256_file(path)
        for path in required
        if path.is_file()
    }
    status = CHECK_WARNING if metadata.get("dirty") else CHECK_PASS
    summary = (
        "Factory checkout is dirty; exact admission tool fingerprints will be recorded."
        if status == CHECK_WARNING
        else "Factory admission toolchain is clean and fingerprinted."
    )
    return AdmissionCheck(
        "FA008", status, summary, {"git": metadata, "fingerprints": fingerprints}
    )


def check(
    *,
    workbench_root: Path,
    source: Path,
    project: str,
    factory_root: Path,
    case_root: Path | None = None,
    update_existing: bool = False,
    allow_dirty_source: bool = False,
    source_git: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workbench_root = workbench_root.resolve()
    source = source.resolve()
    factory_root = factory_root.resolve()
    case_root = case_root.resolve() if case_root is not None else None
    metadata = source_git if source_git is not None else git_metadata(workbench_root)
    source_spec = _load_json(source)
    source_standard_version = source_spec.get("standard_version") if isinstance(source_spec, dict) else None
    checks: list[AdmissionCheck] = [
        _source_clean_check(metadata, allow_dirty_source),
        _target_identity_check(case_root, project),
        _review_check(case_root),
        _assembly_check(case_root),
        _standard_check(workbench_root, factory_root),
        _language_check(source),
        _implementation_obligations_check(source),
        _runtime_persistence_check(source_spec, case_root),
        _external_contract_check(case_root),
        _closure_gaps_check(case_root),
        _projection_drift_check(case_root),
    ]
    validation_check, validation_report = _factory_validation_check(factory_root, source)
    inspector_check, inspector_report = _factory_inspector_check(
        factory_root, project, source
    )
    checks.extend([
        validation_check,
        inspector_check,
        _semantic_check(case_root),
        _target_check(factory_root, project, source, update_existing),
        _factory_toolchain_check(factory_root),
    ])
    blocks = sum(item.status == CHECK_BLOCK for item in checks)
    warnings = sum(item.status == CHECK_WARNING for item in checks)
    passes = sum(item.status == CHECK_PASS for item in checks)
    return {
        "schema_version": REPORT_SCHEMA,
        "stage": "9",
        "status": "READY_TO_EXPORT" if blocks == 0 else "BLOCKED",
        "ready": blocks == 0,
        "project": project,
        "admission_target": {
            "case": case_root.name if case_root is not None else None,
            "case_path": str(case_root) if case_root is not None else None,
            "factory_project": project,
            "factory_project_path": str(factory_root / "projects" / project),
        },
        "source": {
            "path": str(source),
            "sha256": _sha256_file(source),
            "standard_version": source_standard_version,
            "git": metadata,
        },
        "factory_root": str(factory_root),
        "summary": {
            "checks": len(checks),
            "passes": passes,
            "blocks": blocks,
            "warnings": warnings,
        },
        "checks": [item.to_dict() for item in checks],
        "factory_validation": validation_report,
        "factory_inspector": inspector_report,
    }
