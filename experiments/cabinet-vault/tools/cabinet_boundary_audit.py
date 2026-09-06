#!/usr/bin/env python3
"""Classify generated Cabinet backend failures under the box boundary hypothesis."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


AUDIT_SCHEMA_VERSION = "spec_workbench_cabinet_boundary_audit.v0"
SUPPORTED_EVIDENCE_VERSION = "cabinet_generated_backend_failure_evidence.v0"

REMOVE_FROM_CABINET_PRODUCT_SPEC = "remove_from_cabinet_product_spec"
MOVE_TO_GENERIC_HOST_LOWERING = "move_to_generic_host_lowering"
KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC = "keep_and_close_in_cabinet_semantic_spec"

CLASS_DISPOSITIONS: dict[str, str] = {
    "LANGUAGE_RELATION_GAP": MOVE_TO_GENERIC_HOST_LOWERING,
    "PROJECTION_GAP": MOVE_TO_GENERIC_HOST_LOWERING,
    "VERIFICATION_NOT_EXECUTED": MOVE_TO_GENERIC_HOST_LOWERING,
    "BOUNDARY_LEAK": REMOVE_FROM_CABINET_PRODUCT_SPEC,
    "LOWERING_GAP": MOVE_TO_GENERIC_HOST_LOWERING,
    "AUTHORITY_SEMANTIC_GAP": KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC,
    "DOMAIN_SEMANTIC_GAP": KEEP_AND_CLOSE_IN_CABINET_SEMANTIC_SPEC,
}

VALID_VERIFICATION_STATUSES = frozenset({"PASS", "FAIL", "UNVERIFIED", "SKIP"})


@dataclass(frozen=True)
class AuditIssue:
    code: str
    subject: str
    message: str


@dataclass(frozen=True)
class ClassifiedFinding:
    finding_id: str
    summary: str
    finding_class: str
    disposition: str
    verification_required: bool
    declared_verification_status: str | None
    verification_status: str
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class AuditReport:
    schema_version: str
    evidence_version: str | None
    status: str
    verification_gate: str
    findings: tuple[ClassifiedFinding, ...]
    issues: tuple[AuditIssue, ...]


def load_evidence(path: Path) -> dict[str, Any]:
    try:
        import yaml  # type: ignore
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise RuntimeError("PyYAML is required to load boundary-audit evidence") from exc

    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError("boundary-audit evidence must be a mapping")
    return value


def _effective_verification_status(required: bool, declared: str | None) -> str:
    if required and declared in {None, "SKIP", "UNVERIFIED"}:
        return "UNVERIFIED"
    if declared is None:
        return "SKIP"
    return declared


def audit_evidence(definition: dict[str, Any]) -> AuditReport:
    issues: list[AuditIssue] = []
    findings: list[ClassifiedFinding] = []

    evidence_version = definition.get("evidence_version")
    if evidence_version != SUPPORTED_EVIDENCE_VERSION:
        issues.append(
            AuditIssue(
                "UNSUPPORTED_EVIDENCE_VERSION",
                str(evidence_version),
                f"expected {SUPPORTED_EVIDENCE_VERSION}",
            )
        )

    raw_findings = definition.get("findings")
    if not isinstance(raw_findings, list):
        issues.append(
            AuditIssue(
                "INVALID_FINDINGS",
                "findings",
                "findings must be a list",
            )
        )
        raw_findings = []

    seen_ids: set[str] = set()
    for index, raw_finding in enumerate(raw_findings):
        subject = f"findings[{index}]"
        if not isinstance(raw_finding, dict):
            issues.append(AuditIssue("INVALID_FINDING", subject, "finding must be a mapping"))
            continue

        finding_id = raw_finding.get("id")
        if not isinstance(finding_id, str) or not finding_id:
            issues.append(AuditIssue("MISSING_FINDING_ID", subject, "finding id must be non-empty"))
            continue
        if finding_id in seen_ids:
            issues.append(AuditIssue("DUPLICATE_FINDING_ID", finding_id, "finding ids must be unique"))
            continue
        seen_ids.add(finding_id)

        summary = raw_finding.get("summary")
        if not isinstance(summary, str) or not summary:
            issues.append(AuditIssue("MISSING_FINDING_SUMMARY", finding_id, "summary must be non-empty"))
            continue

        finding_class = raw_finding.get("finding_class")
        if not isinstance(finding_class, str) or finding_class not in CLASS_DISPOSITIONS:
            issues.append(
                AuditIssue(
                    "UNKNOWN_FINDING_CLASS",
                    finding_id,
                    "finding_class must be one of the explicitly supported audit classes",
                )
            )
            continue

        raw_evidence = raw_finding.get("evidence")
        if (
            not isinstance(raw_evidence, list)
            or not raw_evidence
            or not all(isinstance(item, str) and item for item in raw_evidence)
        ):
            issues.append(
                AuditIssue(
                    "INVALID_EVIDENCE",
                    finding_id,
                    "evidence must be a non-empty list of strings",
                )
            )
            continue

        required = True
        declared_status: str | None = None
        verification = raw_finding.get("verification")
        if verification is not None and not isinstance(verification, dict):
            issues.append(
                AuditIssue(
                    "INVALID_VERIFICATION",
                    finding_id,
                    "verification must be a mapping when present",
                )
            )
            continue
        if isinstance(verification, dict):
            required_value = verification.get("required", True)
            if not isinstance(required_value, bool):
                issues.append(
                    AuditIssue(
                        "INVALID_VERIFICATION_REQUIRED",
                        finding_id,
                        "verification.required must be boolean",
                    )
                )
                continue
            required = required_value
            declared_value = verification.get("status")
            if declared_value is not None:
                if not isinstance(declared_value, str) or declared_value not in VALID_VERIFICATION_STATUSES:
                    issues.append(
                        AuditIssue(
                            "INVALID_VERIFICATION_STATUS",
                            finding_id,
                            "verification.status must be PASS, FAIL, UNVERIFIED, or SKIP",
                        )
                    )
                    continue
                declared_status = declared_value

        findings.append(
            ClassifiedFinding(
                finding_id=finding_id,
                summary=summary,
                finding_class=finding_class,
                disposition=CLASS_DISPOSITIONS[finding_class],
                verification_required=required,
                declared_verification_status=declared_status,
                verification_status=_effective_verification_status(required, declared_status),
                evidence=tuple(raw_evidence),
            )
        )

    verification_gate = "block" if issues or any(
        finding.verification_required and finding.verification_status != "PASS"
        for finding in findings
    ) else "pass"

    return AuditReport(
        schema_version=AUDIT_SCHEMA_VERSION,
        evidence_version=evidence_version if isinstance(evidence_version, str) else None,
        status="invalid" if issues else "classified",
        verification_gate=verification_gate,
        findings=tuple(findings),
        issues=tuple(issues),
    )


def audit_path(path: Path) -> AuditReport:
    return audit_evidence(load_evidence(path))


def render_json(report: AuditReport) -> str:
    return json.dumps(asdict(report), indent=2, sort_keys=True) + "\n"


def render_human(report: AuditReport) -> str:
    lines = [
        f"Cabinet generated-backend boundary audit: {report.status}",
        f"Evidence: {report.evidence_version}",
        f"Verification gate: {report.verification_gate}",
    ]
    for finding in report.findings:
        lines.append(
            f"- {finding.finding_id}: {finding.finding_class} -> {finding.disposition} "
            f"[verification={finding.verification_status}]"
        )
    for issue in report.issues:
        lines.append(f"- {issue.code}: {issue.subject} — {issue.message}")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = audit_path(args.evidence)
    print(render_json(report) if args.as_json else render_human(report), end="")
    return 0 if report.status == "classified" and report.verification_gate == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
