#!/usr/bin/env python3
"""Execute protected_configuration_kernel verification probes."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from protected_configuration_kernel import (
    ConfigurationBinding,
    ProtectedConfigurationKernel,
    ProtectedConfigurationLeakError,
    ProtectedConfigurationNotReady,
)


PROBE_SCHEMA_VERSION = "spec_workbench_protected_configuration_kernel_probe.v0"


@dataclass(frozen=True)
class ProbeResult:
    probe_id: str
    status: str
    message: str


@dataclass(frozen=True)
class ProbeReport:
    schema_version: str
    provider_id: str
    status: str
    results: tuple[ProbeResult, ...]


def _bindings() -> tuple[ConfigurationBinding, ...]:
    return (
        ConfigurationBinding("database.primary", "SPEC_WORKBENCH_PROBE_DB_SECRET"),
        ConfigurationBinding("vault.signing", "SPEC_WORKBENCH_PROBE_VAULT_SECRET"),
    )


def _probe_missing_required_blocks_ready() -> ProbeResult:
    kernel = ProtectedConfigurationKernel(_bindings(), {"SPEC_WORKBENCH_PROBE_DB_SECRET": "db-secret"})
    try:
        kernel.require_ready()
    except ProtectedConfigurationNotReady:
        return ProbeResult(
            "CONFIG-PROBE-001",
            "PASS",
            "missing required protected configuration blocked provider ready state",
        )
    except Exception as exc:  # pragma: no cover - runtime evidence
        return ProbeResult("CONFIG-PROBE-001", "FAIL", f"unexpected failure: {type(exc).__name__}: {exc}")
    return ProbeResult("CONFIG-PROBE-001", "FAIL", "provider reported ready with missing required secret")


def _probe_no_caller_or_audit_secret_disclosure() -> ProbeResult:
    secret = "probe-secret-material-7f7a5e"
    kernel = ProtectedConfigurationKernel(
        _bindings(),
        {
            "SPEC_WORKBENCH_PROBE_DB_SECRET": secret,
            "SPEC_WORKBENCH_PROBE_VAULT_SECRET": "other-secret",
        },
    )
    try:
        descriptor = kernel.safe_descriptor("database.primary")
        audit_fields = kernel.safe_audit_fields("database.primary")
        if secret in repr(descriptor) or secret in repr(audit_fields):
            return ProbeResult("CONFIG-PROBE-002", "FAIL", "safe metadata disclosed protected material")

        try:
            kernel.use_for_host_provider("database.primary", lambda value: value)
        except ProtectedConfigurationLeakError:
            pass
        else:
            return ProbeResult("CONFIG-PROBE-002", "FAIL", "raw protected value was returned by host use")

        try:
            kernel.use_for_host_provider("database.primary", lambda value: {"dsn": f"wrapped:{value}"})
        except ProtectedConfigurationLeakError:
            pass
        else:
            return ProbeResult("CONFIG-PROBE-002", "FAIL", "embedded protected value escaped in provider result")
    except Exception as exc:  # pragma: no cover - runtime evidence
        return ProbeResult("CONFIG-PROBE-002", "FAIL", f"unexpected failure: {type(exc).__name__}: {exc}")

    return ProbeResult(
        "CONFIG-PROBE-002",
        "PASS",
        "safe descriptors/audit omitted protected material and direct or embedded secret return was rejected",
    )


def _probe_reference_selects_provider_input_without_business_leak() -> ProbeResult:
    db_secret = "db-selected-secret"
    vault_secret = "vault-selected-secret"
    kernel = ProtectedConfigurationKernel(
        _bindings(),
        {
            "SPEC_WORKBENCH_PROBE_DB_SECRET": db_secret,
            "SPEC_WORKBENCH_PROBE_VAULT_SECRET": vault_secret,
        },
    )
    observed: list[str] = []

    def consume(value: str) -> str:
        observed.append(value)
        return "provider-initialized"

    try:
        result = kernel.use_for_host_provider("database.primary", consume)
        descriptor = kernel.safe_descriptor("database.primary")
    except Exception as exc:  # pragma: no cover - runtime evidence
        return ProbeResult("CONFIG-PROBE-003", "FAIL", f"unexpected failure: {type(exc).__name__}: {exc}")

    if observed != [db_secret] or result != "provider-initialized":
        return ProbeResult("CONFIG-PROBE-003", "FAIL", "declared reference selected the wrong provider input")
    text = repr(descriptor)
    if db_secret in text or vault_secret in text or "SPEC_WORKBENCH_PROBE_DB_SECRET" in text:
        return ProbeResult("CONFIG-PROBE-003", "FAIL", "configuration mechanism leaked into caller-visible descriptor")
    if descriptor.get("configuration_reference") != "database.primary":
        return ProbeResult("CONFIG-PROBE-003", "FAIL", "safe descriptor lost the declared reference identity")

    return ProbeResult(
        "CONFIG-PROBE-003",
        "PASS",
        "declared reference selected the exact host provider input while caller-visible metadata contained no secret or source key",
    )


def run_probe() -> ProbeReport:
    results = (
        _probe_missing_required_blocks_ready(),
        _probe_no_caller_or_audit_secret_disclosure(),
        _probe_reference_selects_provider_input_without_business_leak(),
    )
    status = "pass" if all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(PROBE_SCHEMA_VERSION, "protected_configuration_kernel", status, results)


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
