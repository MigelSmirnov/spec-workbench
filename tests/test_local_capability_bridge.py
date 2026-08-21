from __future__ import annotations

from pathlib import Path

import pytest

from local_capability_bridge import (
    CONFIG_BINDINGS,
    PUBLIC_OPERATIONS,
    TARGET_INVOICE_ID,
    TARGET_RESOURCE_SCOPE,
    TARGET_SOURCE_ID,
    LocalCapabilityBridgeError,
    TrustedLocalCapabilityBridge,
)
from local_capability_bridge_probe import run_probe
from protected_configuration_kernel import ProtectedConfigurationNotReady


ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tools" / "local_capability_bridge.py"


def test_bridge_fails_closed_without_protected_configuration():
    bridge = TrustedLocalCapabilityBridge.from_environment({})

    with pytest.raises(ProtectedConfigurationNotReady):
        bridge.start()

    assert bridge.readiness()["ready"] is False


def test_bridge_surface_and_target_are_closed():
    assert PUBLIC_OPERATIONS == (
        "health/readiness",
        "invoice.archive.accept_revision",
        "invoice.source.attach",
    )
    assert TARGET_INVOICE_ID == "invoice-f260001"
    assert TARGET_SOURCE_ID == "source-f260001"
    assert TARGET_RESOURCE_SCOPE == "invoice:invoice-f260001"
    assert not hasattr(TrustedLocalCapabilityBridge, "invoke")


def test_bridge_configuration_references_are_host_owned_and_safe_to_name():
    assert {binding.reference for binding in CONFIG_BINDINGS} == {
        "database.primary_dsn",
        "database.schema",
        "vault.private_root",
        "cabinet_web.reviewed_checkout",
        "authority.synchronization.credential_id",
        "authority.synchronization.credential_material",
        "authority.local_agent.credential_id",
        "authority.local_agent.credential_material",
    }


def test_bridge_rejects_caller_authority_and_storage_fields_before_startup():
    bridge = TrustedLocalCapabilityBridge.from_environment({})
    with pytest.raises(LocalCapabilityBridgeError, match="bridge_not_ready"):
        bridge.accept_revision({"principal": "caller"})


def test_bridge_source_contains_no_old_host_or_generic_dispatcher():
    text = BRIDGE.read_text(encoding="utf-8")
    assert "cabinet_host" not in text
    assert "cabinet_graph_host" not in text
    assert "caller_capability" not in text
    assert "requested_module" not in text
    assert ".execute(" in text
    assert "AuthorityKernel" in text


def test_bridge_runtime_probe_fails_closed_without_provider_configuration():
    report = run_probe({})
    assert report.status == "block"
    assert len(report.results) == 11
    assert {item.status for item in report.results} == {"UNVERIFIED"}
