#!/usr/bin/env python3
"""Narrow local-only bridge for the two protected Cabinet canary capabilities.

The bridge owns host composition and credential selection.  Callers can choose
only one of the fixed public operations; they cannot supply authority, storage,
provider, capability, module, or function identities.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from authority_kernel import (
    LOCAL_AGENT_BOUNDARY,
    SYNCHRONIZATION_BOUNDARY,
    AuthorityKernel,
    CapabilityPolicy,
    CredentialRecord,
    GrantRecord,
    PrincipalRecord,
    credential_digest,
)
from bounded_content_validation_kernel import BoundedContentValidationKernel
from cabinet_web_checkout_sync_adapter import validate_card_with_checkout
from cabinet_web_revision_accept_runtime import (
    CAPABILITY as ACCEPT_CAPABILITY,
    DISCLOSURES as ACCEPT_DISCLOSURES,
    EFFECTS as ACCEPT_EFFECTS,
    CabinetWebRevisionAcceptExecutor,
)
from cabinet_web_source_attach_adapter import CabinetWebSourceAttachAdapter
from invoice_source_attach_models import PUBLICATION_NAMESPACE
from invoice_source_attach_runtime import (
    CAPABILITY as ATTACH_CAPABILITY,
    DISCLOSURES as ATTACH_DISCLOSURES,
    EFFECTS as ATTACH_EFFECTS,
    InvoiceSourceAttachExecutor,
    publication_resource_id,
)
from local_private_byte_vault import LocalPrivateByteVault
from postgres_record_kernel import PostgresRecordKernel
from protected_configuration_kernel import (
    ConfigurationBinding,
    ProtectedConfigurationKernel,
    ProtectedConfigurationNotReady,
)
from typed_schema_kernel import TypedSchemaKernel


TARGET_INVOICE_ID = "invoice-f260001"
TARGET_SOURCE_ID = "source-f260001"
TARGET_RESOURCE_SCOPE = f"invoice:{TARGET_INVOICE_ID}"
SYNC_PRINCIPAL_ID = "cabinet-web-synchronization"
LOCAL_AGENT_PRINCIPAL_ID = "cabinet-local-source-agent"
MAX_SOURCE_BYTES = 32 * 1024 * 1024
ACCEPTED_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "application/pdf"})

CONFIG_BINDINGS = (
    ConfigurationBinding("database.primary_dsn", "CABINET_BRIDGE_POSTGRES_DSN"),
    ConfigurationBinding("database.schema", "CABINET_BRIDGE_POSTGRES_SCHEMA"),
    ConfigurationBinding("vault.private_root", "CABINET_BRIDGE_VAULT_ROOT"),
    ConfigurationBinding("cabinet_web.reviewed_checkout", "CABINET_BRIDGE_CABINET_WEB_ROOT"),
    ConfigurationBinding("authority.synchronization.credential_id", "CABINET_BRIDGE_SYNC_CREDENTIAL_ID"),
    ConfigurationBinding("authority.synchronization.credential_material", "CABINET_BRIDGE_SYNC_CREDENTIAL_MATERIAL"),
    ConfigurationBinding("authority.local_agent.credential_id", "CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_ID"),
    ConfigurationBinding("authority.local_agent.credential_material", "CABINET_BRIDGE_LOCAL_AGENT_CREDENTIAL_MATERIAL"),
)

PUBLIC_OPERATIONS = (
    "health/readiness",
    ACCEPT_CAPABILITY,
    ATTACH_CAPABILITY,
)


class LocalCapabilityBridgeError(RuntimeError):
    """Bounded bridge failure; messages are stable safe codes."""


def _model_dump(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "dict"):
        return value.dict()
    raise LocalCapabilityBridgeError("invalid_executor_result")


def _closed_request(payload: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise LocalCapabilityBridgeError("request_must_be_object")
    extras = set(payload) - allowed
    if extras:
        raise LocalCapabilityBridgeError("undeclared_request_fields")
    return dict(payload)


@dataclass(frozen=True)
class BridgeReadiness:
    ready: bool
    protected_configuration_ready: bool
    providers_ready: bool
    recovery_complete: bool
    transport: str = "local_cli_stdio"
    public_operations: tuple[str, ...] = PUBLIC_OPERATIONS
    target_scope: str = TARGET_RESOURCE_SCOPE

    def safe_payload(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "protected_configuration_ready": self.protected_configuration_ready,
            "providers_ready": self.providers_ready,
            "recovery_complete": self.recovery_complete,
            "transport": self.transport,
            "public_operations": list(self.public_operations),
            "target_scope": self.target_scope,
        }


class TrustedLocalCapabilityBridge:
    """Host-composed, exact-scope bridge over the verified protected executors."""

    def __init__(self, configuration: ProtectedConfigurationKernel) -> None:
        self._configuration = configuration
        self._ready = False
        self._providers_ready = False
        self._recovery_complete = False
        self._records: PostgresRecordKernel | None = None
        self._authority: AuthorityKernel | None = None
        self._accept_executor: CabinetWebRevisionAcceptExecutor | None = None
        self._attach_adapter: CabinetWebSourceAttachAdapter | None = None
        self._recovery_executor: InvoiceSourceAttachExecutor | None = None

    @classmethod
    def from_environment(
        cls, environment: Mapping[str, str] | None = None
    ) -> "TrustedLocalCapabilityBridge":
        return cls(ProtectedConfigurationKernel.from_environment(CONFIG_BINDINGS, environment))

    def _resolve(self, reference: str, consumer):
        return self._configuration.use_for_host_provider(reference, consumer)

    def _authority_kernel(self) -> AuthorityKernel:
        def build(sync_id: str, local_id: str, sync_material: str, local_material: str):
            return AuthorityKernel(
                principals=(
                    PrincipalRecord(SYNC_PRINCIPAL_ID, "service"),
                    PrincipalRecord(LOCAL_AGENT_PRINCIPAL_ID, "agent"),
                ),
                credentials=(
                    CredentialRecord(
                        sync_id,
                        SYNC_PRINCIPAL_ID,
                        SYNCHRONIZATION_BOUNDARY,
                        credential_digest(sync_material),
                    ),
                    CredentialRecord(
                        local_id,
                        LOCAL_AGENT_PRINCIPAL_ID,
                        LOCAL_AGENT_BOUNDARY,
                        credential_digest(local_material),
                    ),
                ),
                grants=(
                    GrantRecord(
                        "grant-f260001-revision-accept",
                        SYNC_PRINCIPAL_ID,
                        ACCEPT_CAPABILITY,
                        TARGET_RESOURCE_SCOPE,
                        effect_scope=ACCEPT_EFFECTS,
                        disclosure_scope=ACCEPT_DISCLOSURES,
                    ),
                    GrantRecord(
                        "grant-f260001-source-attach",
                        LOCAL_AGENT_PRINCIPAL_ID,
                        ATTACH_CAPABILITY,
                        TARGET_RESOURCE_SCOPE,
                        effect_scope=ATTACH_EFFECTS,
                        disclosure_scope=ATTACH_DISCLOSURES,
                    ),
                ),
                policies=(
                    CapabilityPolicy(
                        ACCEPT_CAPABILITY,
                        effects=ACCEPT_EFFECTS,
                        disclosure_allow=ACCEPT_DISCLOSURES,
                    ),
                    CapabilityPolicy(
                        ATTACH_CAPABILITY,
                        effects=ATTACH_EFFECTS,
                        disclosure_allow=ATTACH_DISCLOSURES,
                    ),
                ),
            )

        return self._resolve(
            "authority.synchronization.credential_id",
            lambda sync_id: self._resolve(
                "authority.local_agent.credential_id",
                lambda local_id: self._resolve(
                    "authority.synchronization.credential_material",
                    lambda sync_material: self._resolve(
                        "authority.local_agent.credential_material",
                        lambda local_material: build(
                            sync_id, local_id, sync_material, local_material
                        ),
                    ),
                ),
            ),
        )

    def start(self) -> None:
        self._configuration.require_ready()
        records = self._resolve(
            "database.primary_dsn",
            lambda dsn: self._resolve(
                "database.schema", lambda schema: PostgresRecordKernel(dsn, schema=schema)
            ),
        )
        records.initialize()
        vault = self._resolve(
            "vault.private_root",
            lambda root: LocalPrivateByteVault(Path(root), max_size_bytes=MAX_SOURCE_BYTES),
        )
        content_validation = BoundedContentValidationKernel(
            max_size_bytes=MAX_SOURCE_BYTES,
            accepted_media_types=ACCEPTED_MEDIA_TYPES,
        )
        typed_schema = TypedSchemaKernel()
        authority = self._authority_kernel()
        accept_executor = self._resolve(
            "cabinet_web.reviewed_checkout",
            lambda checkout_root: CabinetWebRevisionAcceptExecutor(
                authority=authority,
                typed_schema=typed_schema,
                records=records,
                card_validator=lambda card: validate_card_with_checkout(
                    card, cabinet_web_root=checkout_root
                ),
            ),
        )
        attach_adapter = CabinetWebSourceAttachAdapter(
            authority=authority,
            typed_schema=typed_schema,
            records=records,
            byte_vault=vault,
            content_validation=content_validation,
        )
        recovery_executor = InvoiceSourceAttachExecutor(
            authority=authority,
            typed_schema=typed_schema,
            records=records,
            byte_vault=vault,
            content_validation=content_validation,
        )

        self._providers_ready = True
        publication = records.read_record(
            PUBLICATION_NAMESPACE,
            publication_resource_id(TARGET_INVOICE_ID, TARGET_SOURCE_ID),
        )
        if publication is not None and publication.payload.get("state") in {
            "metadata_committed",
            "published",
        }:
            recovery_executor.recover_pending_publication(
                invoice_id=TARGET_INVOICE_ID,
                source_id=TARGET_SOURCE_ID,
            )
        self._recovery_complete = True
        self._records = records
        self._authority = authority
        self._accept_executor = accept_executor
        self._attach_adapter = attach_adapter
        self._recovery_executor = recovery_executor
        self._ready = True

    def readiness(self) -> dict[str, Any]:
        return BridgeReadiness(
            ready=self._ready,
            protected_configuration_ready=self._ready,
            providers_ready=self._providers_ready,
            recovery_complete=self._recovery_complete,
        ).safe_payload()

    def _require_started(self) -> None:
        if not self._ready or self._accept_executor is None or self._attach_adapter is None:
            raise LocalCapabilityBridgeError("bridge_not_ready")

    def accept_revision(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self._require_started()
        value = _closed_request(request, frozenset({"delivery", "interaction_id"}))
        delivery = value.get("delivery")
        if not isinstance(delivery, Mapping):
            raise LocalCapabilityBridgeError("delivery_required")
        if delivery.get("invoice_id") != TARGET_INVOICE_ID:
            raise LocalCapabilityBridgeError("exact_invoice_scope_required")
        interaction_id = value.get("interaction_id")
        if not isinstance(interaction_id, str) or not interaction_id:
            raise LocalCapabilityBridgeError("interaction_id_required")

        assert self._accept_executor is not None
        result = self._resolve(
            "authority.synchronization.credential_id",
            lambda credential_id: self._resolve(
                "authority.synchronization.credential_material",
                lambda material: self._accept_executor.execute(
                    delivery,
                    credential_id=credential_id,
                    credential_material=material,
                    interaction_id=interaction_id,
                ),
            ),
        )
        return _model_dump(result)

    def attach_source(self, request: Mapping[str, Any]) -> dict[str, Any]:
        self._require_started()
        value = _closed_request(
            request,
            frozenset(
                {"invoice_id", "source_id", "filename", "content_base64", "interaction_id"}
            ),
        )
        if value.get("invoice_id") != TARGET_INVOICE_ID:
            raise LocalCapabilityBridgeError("exact_invoice_scope_required")
        if value.get("source_id") != TARGET_SOURCE_ID:
            raise LocalCapabilityBridgeError("exact_source_identity_required")
        filename = value.get("filename")
        interaction_id = value.get("interaction_id")
        encoded = value.get("content_base64")
        if not isinstance(filename, str) or not filename:
            raise LocalCapabilityBridgeError("filename_required")
        if not isinstance(interaction_id, str) or not interaction_id:
            raise LocalCapabilityBridgeError("interaction_id_required")
        if not isinstance(encoded, str) or not encoded:
            raise LocalCapabilityBridgeError("content_base64_required")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError) as exc:
            raise LocalCapabilityBridgeError("invalid_content_base64") from exc
        if not content or len(content) > MAX_SOURCE_BYTES:
            raise LocalCapabilityBridgeError("source_content_out_of_bounds")

        assert self._attach_adapter is not None
        result = self._resolve(
            "authority.local_agent.credential_id",
            lambda credential_id: self._resolve(
                "authority.local_agent.credential_material",
                lambda material: self._attach_adapter.execute(
                    invoice_id=TARGET_INVOICE_ID,
                    source_id=TARGET_SOURCE_ID,
                    filename=filename,
                    content=content,
                    credential_id=credential_id,
                    credential_material=material,
                    interaction_id=interaction_id,
                ),
            ),
        )
        return _model_dump(result)


def _read_request() -> dict[str, Any]:
    try:
        value = json.load(sys.stdin)
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalCapabilityBridgeError("invalid_json_request") from exc
    if not isinstance(value, dict):
        raise LocalCapabilityBridgeError("request_must_be_object")
    return value


def _safe_error(code: str) -> dict[str, Any]:
    return {"ok": False, "error_code": code}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Trusted local Cabinet capability bridge")
    parser.add_argument(
        "operation",
        choices=("readiness", "accept-revision", "attach-source"),
    )
    args = parser.parse_args(argv)
    bridge = TrustedLocalCapabilityBridge.from_environment(os.environ)
    try:
        bridge.start()
        if args.operation == "readiness":
            output = {"ok": True, **bridge.readiness()}
        elif args.operation == "accept-revision":
            output = {"ok": True, "receipt": bridge.accept_revision(_read_request())}
        else:
            output = {"ok": True, "attachment": bridge.attach_source(_read_request())}
    except ProtectedConfigurationNotReady:
        output = _safe_error("protected_configuration_not_ready")
    except LocalCapabilityBridgeError as exc:
        output = _safe_error(str(exc))
    except Exception:
        output = _safe_error("bridge_operation_failed")
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if output.get("ok") is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
