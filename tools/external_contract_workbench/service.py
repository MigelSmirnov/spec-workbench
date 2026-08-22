from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from external_contract_workbench.model import (
    AUTHORITIES,
    BINDING_FIELDS,
    CONTRACT_FIELDS,
    EVIDENCE_FIELDS,
    REPORT_SCHEMA,
    ROOT_FIELDS,
    SCHEMA,
    STATUSES,
    SUBJECT_FIELDS,
)


MANIFEST = "70_external_contract_evidence.json"
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ADDRESS_RE = re.compile(r"^(?:config|models|rules)(?:\.[A-Za-z_][A-Za-z0-9_]*)+$")


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def canonical_value_sha(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return _sha_bytes(payload)


def _file_sha(path: Path) -> str:
    return _sha_bytes(path.read_bytes())


def _finding(code: str, message: str, **context: Any) -> dict[str, Any]:
    return {"severity": "error", "code": code, "message": message, **context}


def _exact_shape(
    value: Any, expected: set[str], location: str, findings: list[dict[str, Any]]
) -> bool:
    if not isinstance(value, dict):
        findings.append(_finding("invalid_shape", f"{location} must be an object", location=location))
        return False
    actual = set(value)
    if actual != expected:
        findings.append(_finding(
            "invalid_shape",
            f"{location} fields differ from the closed schema",
            location=location,
            missing=sorted(expected - actual),
            extra=sorted(actual - expected),
        ))
        return False
    return True


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _resolve(spec: dict[str, Any], address: str) -> tuple[bool, Any]:
    current: Any = spec
    for part in address.split("."):
        if not isinstance(current, dict) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _inside_project(project: Path, relative: Any) -> Path | None:
    if not _nonempty_text(relative):
        return None
    candidate_text = str(relative)
    candidate = Path(candidate_text)
    if candidate.is_absolute():
        return None
    resolved = (project / candidate).resolve()
    root = project.resolve()
    if resolved == root or root not in resolved.parents:
        return None
    return resolved


def _required_contract_ids(project: Path) -> tuple[set[str], list[dict[str, Any]]]:
    required: set[str] = set()
    findings: list[dict[str, Any]] = []
    for path in sorted(project.glob("70_*_closure.json")):
        try:
            closure = _load(path)
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            findings.append(_finding("closure_load_error", str(exc), artifact=path.name))
            continue
        if not isinstance(closure, dict) or "external_contract_evidence_ids" not in closure:
            continue
        ids = closure.get("external_contract_evidence_ids")
        if (
            not isinstance(ids, list)
            or not ids
            or any(not _nonempty_text(item) for item in ids)
            or len(ids) != len(set(ids))
        ):
            findings.append(_finding(
                "invalid_external_contract_requirement",
                "external_contract_evidence_ids must be a non-empty unique string list",
                artifact=path.name,
            ))
            continue
        required.update(ids)
    return required, findings


def coverage(project: Path) -> dict[str, Any]:
    manifest_path = project / MANIFEST
    required_ids, requirement_findings = _required_contract_ids(project)
    if not manifest_path.is_file():
        errors = len(requirement_findings) + (1 if required_ids else 0)
        findings = list(requirement_findings)
        if required_ids:
            findings.append(_finding(
                "missing_external_contract_manifest",
                "a closure requires external-contract evidence but the manifest is absent",
                required_contract_ids=sorted(required_ids),
            ))
        return {
            "schema_version": REPORT_SCHEMA,
            "project_root": project.resolve().name,
            "status": "not_applicable" if errors == 0 else "invalid",
            "manifest": None,
            "manifest_sha256": None,
            "summary": {
                "contracts": 0, "active": 0, "superseded": 0,
                "bindings": 0, "errors": errors, "handoff_ready": errors == 0,
            },
            "contracts": [],
            "findings": findings,
        }

    findings: list[dict[str, Any]] = list(requirement_findings)
    try:
        manifest = _load(manifest_path)
        spec = _load(project / "global_spec.json")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        return {
            "schema_version": REPORT_SCHEMA,
            "project_root": project.resolve().name,
            "status": "invalid",
            "manifest": str(manifest_path),
            "manifest_sha256": _file_sha(manifest_path),
            "summary": {
                "contracts": 0, "active": 0, "superseded": 0,
                "bindings": 0, "errors": 1, "handoff_ready": False,
            },
            "contracts": [],
            "findings": [_finding("load_error", str(exc))],
        }

    if not _exact_shape(manifest, ROOT_FIELDS, "manifest", findings):
        contracts: list[Any] = []
    else:
        if manifest.get("schema_version") != SCHEMA:
            findings.append(_finding("unsupported_schema", f"schema_version must be {SCHEMA!r}"))
        if manifest.get("status") != "closed":
            findings.append(_finding("manifest_not_closed", "external-contract manifest status must be closed"))
        contracts = manifest.get("contracts")
        if not isinstance(contracts, list) or not contracts:
            findings.append(_finding("invalid_contracts", "contracts must be a non-empty list"))
            contracts = []

    spec_modules = set(spec.get("module_order", [])) if isinstance(spec, dict) else set()
    ids: dict[str, dict[str, Any]] = {}
    active_addresses: dict[str, str] = {}
    normalized: list[dict[str, Any]] = []
    binding_count = 0

    for index, record in enumerate(contracts):
        location = f"contracts[{index}]"
        if not _exact_shape(record, CONTRACT_FIELDS, location, findings):
            continue
        contract_id = record.get("id")
        if not _nonempty_text(contract_id):
            findings.append(_finding("invalid_contract_id", "id must be non-empty", location=location))
            continue
        if contract_id in ids:
            findings.append(_finding("duplicate_contract_id", f"duplicate id {contract_id!r}", contract_id=contract_id))
            continue
        ids[contract_id] = record
        status = record.get("status")
        if status not in STATUSES:
            findings.append(_finding("invalid_status", f"unsupported status {status!r}", contract_id=contract_id))
        if record.get("authority") not in AUTHORITIES:
            findings.append(_finding("invalid_authority", "authority is outside the closed registry", contract_id=contract_id))
        if not _nonempty_text(record.get("verified_by")):
            findings.append(_finding("invalid_verified_by", "verified_by must identify the reviewer or controlled run owner", contract_id=contract_id))

        subject = record.get("subject")
        if _exact_shape(subject, SUBJECT_FIELDS, f"{location}.subject", findings):
            for field in SUBJECT_FIELDS:
                if not _nonempty_text(subject.get(field)):
                    findings.append(_finding("invalid_subject", f"subject.{field} must be non-empty", contract_id=contract_id))

        verified_at = record.get("verified_at")
        try:
            if not isinstance(verified_at, str) or not verified_at.endswith("Z"):
                raise ValueError
            datetime.fromisoformat(verified_at.removesuffix("Z") + "+00:00")
        except ValueError:
            findings.append(_finding("invalid_verified_at", "verified_at must be an RFC3339 UTC timestamp", contract_id=contract_id))

        evidence = record.get("evidence")
        evidence_path: Path | None = None
        if _exact_shape(evidence, EVIDENCE_FIELDS, f"{location}.evidence", findings):
            for field in ("run_id", "result"):
                if not _nonempty_text(evidence.get(field)):
                    findings.append(_finding("invalid_evidence", f"evidence.{field} must be non-empty", contract_id=contract_id))
            evidence_path = _inside_project(project, evidence.get("artifact"))
            if evidence_path is None:
                findings.append(_finding("escaping_evidence_artifact", "evidence artifact must be a relative project file", contract_id=contract_id))
            elif not evidence_path.is_file():
                findings.append(_finding("missing_evidence_artifact", "evidence artifact does not exist", contract_id=contract_id))
            expected_sha = evidence.get("sha256")
            if not isinstance(expected_sha, str) or not SHA_RE.fullmatch(expected_sha):
                findings.append(_finding("invalid_evidence_sha", "evidence.sha256 must be a lowercase sha256 fingerprint", contract_id=contract_id))
            elif evidence_path is not None and evidence_path.is_file():
                actual_sha = _file_sha(evidence_path)
                if actual_sha != expected_sha:
                    findings.append(_finding("evidence_sha_mismatch", "evidence artifact changed after verification", contract_id=contract_id, expected=expected_sha, actual=actual_sha))

        modules = record.get("modules")
        if not isinstance(modules, list) or not modules or any(not _nonempty_text(item) for item in modules):
            findings.append(_finding("invalid_modules", "modules must be a non-empty string list", contract_id=contract_id))
            modules = []
        elif len(modules) != len(set(modules)):
            findings.append(_finding("duplicate_module", "modules must be unique", contract_id=contract_id))
        for module in modules:
            if module not in spec_modules:
                findings.append(_finding("unknown_module", f"unknown assembled module {module!r}", contract_id=contract_id))

        supersedes = record.get("supersedes")
        superseded_by = record.get("superseded_by")
        if not isinstance(supersedes, list) or any(not _nonempty_text(item) for item in supersedes) or len(supersedes) != len(set(supersedes)):
            findings.append(_finding("invalid_supersedes", "supersedes must be a unique string list", contract_id=contract_id))
            supersedes = []
        if superseded_by is not None and not _nonempty_text(superseded_by):
            findings.append(_finding("invalid_superseded_by", "superseded_by must be null or a contract id", contract_id=contract_id))
        if status == "active" and superseded_by is not None:
            findings.append(_finding("active_contract_superseded", "active contract cannot declare superseded_by", contract_id=contract_id))
        if status == "superseded" and not _nonempty_text(superseded_by):
            findings.append(_finding("missing_superseded_by", "superseded contract must name its replacement", contract_id=contract_id))

        bindings = record.get("bindings")
        if not isinstance(bindings, list) or not bindings:
            findings.append(_finding("invalid_bindings", "bindings must be a non-empty list", contract_id=contract_id))
            bindings = []
        seen_bindings: set[str] = set()
        for binding_index, binding in enumerate(bindings):
            binding_location = f"{location}.bindings[{binding_index}]"
            if not _exact_shape(binding, BINDING_FIELDS, binding_location, findings):
                continue
            address = binding.get("address")
            value_sha = binding.get("value_sha256")
            if not isinstance(address, str) or not ADDRESS_RE.fullmatch(address):
                findings.append(_finding("invalid_binding_address", "binding address must be a config/models/rules dotted address", contract_id=contract_id, location=binding_location))
                continue
            if address in seen_bindings:
                findings.append(_finding("duplicate_binding", f"duplicate binding {address!r}", contract_id=contract_id))
                continue
            seen_bindings.add(address)
            binding_count += 1
            if not isinstance(value_sha, str) or not SHA_RE.fullmatch(value_sha):
                findings.append(_finding("invalid_value_sha", "value_sha256 must be a lowercase sha256 fingerprint", contract_id=contract_id, address=address))
                continue
            resolved, value = _resolve(spec, address)
            if not resolved:
                findings.append(_finding("unresolved_binding", f"binding does not resolve: {address}", contract_id=contract_id, address=address))
                continue
            if status == "active":
                previous = active_addresses.get(address)
                if previous is not None:
                    findings.append(_finding("competing_active_binding", f"address is active in both {previous!r} and {contract_id!r}", contract_id=contract_id, address=address))
                else:
                    active_addresses[address] = contract_id
                actual_value_sha = canonical_value_sha(value)
                if actual_value_sha != value_sha:
                    findings.append(_finding("verified_value_changed", "assembled external fact differs from verified evidence", contract_id=contract_id, address=address, expected=value_sha, actual=actual_value_sha))

        normalized.append(record)

    for contract_id, record in ids.items():
        replacement = record.get("superseded_by")
        if isinstance(replacement, str):
            target = ids.get(replacement)
            if target is None:
                findings.append(_finding("unknown_replacement", f"unknown replacement {replacement!r}", contract_id=contract_id))
            elif contract_id not in target.get("supersedes", []):
                findings.append(_finding("nonreciprocal_supersession", "replacement must reciprocally list superseded id", contract_id=contract_id))
        for previous in record.get("supersedes", []) if isinstance(record.get("supersedes"), list) else []:
            source = ids.get(previous)
            if source is None:
                findings.append(_finding("unknown_superseded_contract", f"unknown superseded id {previous!r}", contract_id=contract_id))
            elif source.get("superseded_by") != contract_id:
                findings.append(_finding("nonreciprocal_supersession", "superseded contract must point to its replacement", contract_id=contract_id))

    for required_id in sorted(required_ids):
        record = ids.get(required_id)
        if record is None:
            findings.append(_finding(
                "missing_required_external_contract",
                f"required external contract {required_id!r} is absent",
                contract_id=required_id,
            ))
        elif record.get("status") != "active":
            findings.append(_finding(
                "required_external_contract_not_active",
                f"required external contract {required_id!r} is not active",
                contract_id=required_id,
            ))

    active = sum(record.get("status") == "active" for record in normalized)
    superseded = sum(record.get("status") == "superseded" for record in normalized)
    errors = len(findings)
    return {
        "schema_version": REPORT_SCHEMA,
        "project_root": project.resolve().name,
        "status": "closed" if errors == 0 else "invalid",
        "manifest": str(manifest_path),
        "manifest_sha256": _file_sha(manifest_path),
        "summary": {
            "contracts": len(normalized), "active": active,
            "superseded": superseded, "bindings": binding_count,
            "errors": errors, "handoff_ready": errors == 0,
        },
        "contracts": normalized,
        "findings": findings,
    }


def module_evidence(project: Path, module: str) -> list[dict[str, Any]]:
    report = coverage(project)
    if not report["summary"]["handoff_ready"]:
        return []
    return [
        record for record in report["contracts"]
        if record.get("status") == "active" and module in record.get("modules", [])
    ]
