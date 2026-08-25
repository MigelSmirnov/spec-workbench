from __future__ import annotations

import pytest

from protected_configuration_kernel import (
    ConfigurationBinding,
    ProtectedConfigurationKernel,
    ProtectedConfigurationLeakError,
    ProtectedConfigurationNotReady,
)
from protected_configuration_kernel_probe import run_probe


def bindings():
    return (
        ConfigurationBinding("database.primary", "TEST_DB_SECRET"),
        ConfigurationBinding("vault.signing", "TEST_VAULT_SECRET"),
    )


def test_missing_required_binding_blocks_ready_state():
    kernel = ProtectedConfigurationKernel(bindings(), {"TEST_DB_SECRET": "db"})

    with pytest.raises(ProtectedConfigurationNotReady):
        kernel.require_ready()


def test_safe_descriptor_and_audit_do_not_contain_source_key_or_secret():
    secret = "private-material"
    kernel = ProtectedConfigurationKernel(
        bindings(),
        {"TEST_DB_SECRET": secret, "TEST_VAULT_SECRET": "vault"},
    )

    descriptor = kernel.safe_descriptor("database.primary")
    audit = kernel.safe_audit_fields("database.primary")

    for value in (descriptor, audit):
        text = repr(value)
        assert secret not in text
        assert "TEST_DB_SECRET" not in text
        assert value["configuration_reference"] == "database.primary"


def test_host_provider_use_rejects_returning_secret_material():
    secret = "private-material"
    kernel = ProtectedConfigurationKernel(
        bindings(),
        {"TEST_DB_SECRET": secret, "TEST_VAULT_SECRET": "vault"},
    )

    with pytest.raises(ProtectedConfigurationLeakError):
        kernel.use_for_host_provider("database.primary", lambda value: value)

    with pytest.raises(ProtectedConfigurationLeakError):
        kernel.use_for_host_provider("database.primary", lambda value: {"wrapped": f"x:{value}"})


def test_reference_selects_exact_provider_input_without_exposing_it():
    kernel = ProtectedConfigurationKernel(
        bindings(),
        {"TEST_DB_SECRET": "db", "TEST_VAULT_SECRET": "vault"},
    )
    observed: list[str] = []

    result = kernel.use_for_host_provider(
        "vault.signing",
        lambda value: observed.append(value) or "provider-ready",
    )

    assert result == "provider-ready"
    assert observed == ["vault"]
    assert kernel.safe_descriptor("vault.signing") == {
        "configuration_reference": "vault.signing",
        "configured": True,
        "protected": True,
    }


def test_full_protected_configuration_probe_passes():
    report = run_probe()

    assert report.status == "pass"
    assert [item.probe_id for item in report.results] == [
        "CONFIG-PROBE-001",
        "CONFIG-PROBE-002",
        "CONFIG-PROBE-003",
    ]
    assert {item.status for item in report.results} == {"PASS"}
