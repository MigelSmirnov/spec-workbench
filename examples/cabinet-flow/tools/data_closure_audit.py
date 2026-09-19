#!/usr/bin/env python3
"""Exact Cabinet Flow pre-contract structured-data audit."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_RELEASE_CEILINGS = {
    "sandbox_wall_time_ms_max": 30000,
    "sandbox_cpu_time_ms_max": 20000,
    "sandbox_memory_bytes_max": 536870912,
    "sandbox_output_bytes_max": 67108864,
    "sandbox_scratch_bytes_max": 268435456,
    "sandbox_process_count_max": 8,
    "implementation_code_bytes_max": 4194304,
    "stored_value_bytes_max": 1048576,
    "trial_fixture_bytes_max": 67108864,
    "run_spool_file_bytes_max": 134217728,
    "run_spool_total_bytes_max": 536870912,
    "surface_request_bytes_max": 134217728,
    "bounded_text_bytes_max": 16384,
    "failure_detail_bytes_max": 4096,
    "page_size_default": 50,
    "page_size_max": 200,
    "transport_timeout_ms_max": 60000,
}

EXPECTED_RETENTION = {
    "run_evidence_days": 90,
    "personal_data_run_evidence_days": 30,
    "trial_corpus_lifetime": "installation",
    "approval_evidence_lifetime": "installation",
    "longest_reference_wins": True,
    "non_terminal_run_blocks_expiry": True,
}

EXPECTED_KERNEL_TIME = {
    "canonical_type": "KernelInstant",
    "representation": "epoch_us",
    "production_wall_clock_primitive": "time.time_ns",
    "production_samples_per_now": 1,
    "nanoseconds_per_epoch_us": 1000,
    "elapsed_duration_primitive": "time.monotonic_ns",
    "service_timestamp_is_kernel_time": False,
    "cross_service_ordering_from_service_timestamps": False,
}

EXPECTED_AUTH_THROTTLE = {
    "delay_seconds_by_failure_count_1_to_9": [0, 0, 0, 0, 1, 2, 4, 8, 16],
    "block_after_failures": 10,
    "block_seconds": 900,
    "blocked_attempt_increments_count": False,
    "blocked_attempt_extends_block": False,
    "successful_authentication_resets": True,
    "survives_restart": True,
}

EXPECTED_RETRY = {
    "delay_seconds_by_ordinal_1_to_6": [1, 2, 5, 10, 30, 60],
    "delay_seconds_after_ordinal_6": 60,
    "jitter": False,
    "timed_wait_reasons": ["service_unreachable", "outcome_unknown"],
    "wake_before_deadline_invokes": False,
    "restart_resets_ordinal": False,
    "retry_count_causes_run_failure": False,
}

EXPECTED_PERSISTENCE = {
    "SemanticAxis": "master",
    "SemanticAxisRevision": "issued",
    "SemanticTerm": "master",
    "SemanticTermRevision": "issued",
    "SemanticRelation": "master",
    "SemanticRelationRevision": "issued",
    "OwnerPrincipal": "master",
    "AgentDelegation": "master",
    "AuthenticationThrottleState": "master",
    "OperationBinding": "master",
    "OperationBindingVersion": "issued",
    "Flow": "master",
    "FlowVersion": "issued",
    "FlowProof": "issued",
    "FlowActivation": "issued",
    "StoredValue": "master",
    "FlowRun": "master",
    "NodeExecution": "issued",
    "EffectApproval": "issued",
    "StandingGrant": "master",
    "OutcomeReconciliation": "issued",
    "VocabularyProposal": "master",
    "Slot": "master",
    "SlotContractVersion": "issued",
    "SandboxRuntimeRevision": "issued",
    "Implementation": "issued",
    "TrialCase": "master",
    "TrialExecution": "issued",
    "AdmissionVerdict": "issued",
    "SlotActivation": "issued",
}


def _compare(findings: list[str], label: str, actual: object, expected: object) -> None:
    if actual != expected:
        findings.append(f"{label}: expected {expected!r}, got {actual!r}")


def audit(project: Path) -> list[str]:
    payload = json.loads((project / "60_data_closure.json").read_text(encoding="utf-8"))
    sections = payload.get("sections") or {}
    rules = sections.get("rules") or {}
    findings: list[str] = []

    _compare(findings, "config.release_ceilings", (sections.get("config") or {}).get("release_ceilings"), EXPECTED_RELEASE_CEILINGS)
    _compare(findings, "rules.retention", rules.get("retention"), EXPECTED_RETENTION)
    _compare(findings, "rules.kernel_time", rules.get("kernel_time"), EXPECTED_KERNEL_TIME)
    _compare(findings, "rules.authentication_throttle", rules.get("authentication_throttle"), EXPECTED_AUTH_THROTTLE)
    _compare(findings, "rules.retry_backoff", rules.get("retry_backoff"), EXPECTED_RETRY)

    persistence = sections.get("persistence") or {}
    actual_persistence = {
        name: declaration.get("class")
        for name, declaration in persistence.items()
        if isinstance(declaration, dict)
    }
    _compare(findings, "persistence classes", actual_persistence, EXPECTED_PERSISTENCE)

    if payload.get("unresolved") != []:
        findings.append("60_data_closure.json: unresolved must be empty before State 6")

    placements = payload.get("placements")
    if not isinstance(placements, list):
        findings.append("60_data_closure.json: placements must be a list")
    else:
        addresses = [item.get("address") for item in placements if isinstance(item, dict)]
        if len(addresses) != len(set(addresses)):
            findings.append("60_data_closure.json: placement addresses must be unique")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project", type=Path)
    args = parser.parse_args()
    findings = audit(args.project.resolve())
    if findings:
        for finding in findings:
            print(finding)
        print(f"FAIL: {len(findings)} structured-data finding(s)")
        return 1
    print("PASS: Cabinet Flow structured data closure matches accepted release/policy facts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
