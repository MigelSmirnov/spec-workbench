"""One subprocess boundary to the Factory's canonical spec validator.

Assembly and admission consume the same verdict on the same source bytes.
No validation rules are implemented here.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def resolve_factory_root() -> Path:
    override = os.environ.get("SPEC_WORKBENCH_FACTORY_ROOT")
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[2] / "code_factory"


def validate_source(source: Path, factory_root: Path | None = None) -> dict:
    root = factory_root if factory_root is not None else resolve_factory_root()
    validator = root / "tools" / "validate_spec.py"
    evidence = {"validator": str(validator), "ready": False, "report": None}
    try:
        source_bytes = source.read_bytes()
        spec = json.loads(source_bytes)
        expected = "sha256:" + hashlib.sha256(
            json.dumps(spec, sort_keys=True, ensure_ascii=False).encode("utf-8")
        ).hexdigest()
        evidence["expected_spec_sha"] = expected
        evidence["validator_sha256"] = hashlib.sha256(validator.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix="workbench-validation-") as scratch:
            report_path = Path(scratch) / "report.json"
            result = subprocess.run(
                [sys.executable, str(validator), str(source.resolve()),
                 "--out", str(report_path), "--quiet"],
                cwd=root, capture_output=True, text=True, check=False, timeout=60,
            )
            evidence["returncode"] = result.returncode
            report = json.loads(report_path.read_text(encoding="utf-8"))
        if not isinstance(report, dict) or not isinstance(report.get("summary"), dict):
            raise ValueError("invalid validator report shape")
        if not isinstance(report.get("findings"), list):
            raise ValueError("validator report has no findings list")
        if source.read_bytes() != source_bytes:
            raise ValueError("source changed during validation")
        if hashlib.sha256(validator.read_bytes()).hexdigest() != evidence["validator_sha256"]:
            raise ValueError("validator changed during validation")
        evidence["report"] = report
        evidence["ready"] = (
            result.returncode == 0 and report.get("status") == "PASS"
            and type(report["summary"].get("error")) is int and report["summary"]["error"] == 0
            and type(report["summary"].get("warning", 0)) is int and report["summary"].get("warning", 0) == 0
            and all(isinstance(item, dict) and item.get("severity") not in {"error", "warning", "BLOCK"}
                    for item in report["findings"])
            and report.get("spec_sha") == expected
        )
        evidence["reason"] = "accepted" if evidence["ready"] else "Factory validation did not pass for this spec"
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        evidence["reason"] = f"Factory validation unavailable: {error}"
    return evidence


def assembly_check(project: Path, factory_root: Path | None = None) -> dict:
    evidence = validate_source(project / "global_spec.json", factory_root)
    report = evidence["report"] or {}
    findings = list(report.get("findings", []))
    if not evidence["ready"]:
        findings.append({"severity": "error", "code": "factory_validation_blocked",
                         "message": evidence["reason"]})
    return {
        "schema_version": "spec_workbench_factory_validation.v1",
        "ready": evidence["ready"],
        "summary": {"errors": 0 if evidence["ready"] else max(1, len(findings)),
                    "evidence": evidence},
        "findings": findings,
    }
