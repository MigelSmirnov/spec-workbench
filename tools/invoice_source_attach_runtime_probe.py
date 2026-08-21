#!/usr/bin/env python3
"""Execute ATTACH-PROBE-001..007 against the first real source-attach runtime case."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import uuid
from dataclasses import asdict, dataclass
from io import BytesIO
from pathlib import Path

from authority_kernel import (
    LOCAL_AGENT_BOUNDARY,
    AuthorityKernel,
    AuthorizationDenied,
    CapabilityPolicy,
    CredentialRecord,
    GrantRecord,
    PrincipalRecord,
    credential_digest,
)
from bounded_content_validation_kernel import BoundedContentValidationKernel
from invoice_source_attach_models import INVOICE_NAMESPACE, PUBLICATION_NAMESPACE
from invoice_source_attach_runtime import (
    DISCLOSURES,
    EFFECTS,
    InvoiceSourceAttachExecutionError,
    InvoiceSourceAttachExecutor,
    InvoiceSourceAttachRejected,
    publication_resource_id,
    seed_expected_missing_source,
)
from local_private_byte_vault import LocalPrivateByteVault
from postgres_record_kernel import PostgresRecordKernel
from protected_configuration_kernel import (
    ConfigurationBinding,
    ProtectedConfigurationKernel,
    ProtectedConfigurationNotReady,
)
from typed_schema_kernel import TypedSchemaKernel, TypedSchemaValidationError


PROBE_SCHEMA_VERSION = "spec_workbench_invoice_source_attach_runtime_probe.v0"
DB_ENV = "SPEC_WORKBENCH_TEST_POSTGRES_DSN"
VAULT_ENV = "SPEC_WORKBENCH_ATTACH_VAULT_ROOT"
AGENT_SECRET = "attach-probe-agent-secret-3cb498"
MAX_BYTES = 50 * 1024 * 1024
ACCEPTED_MEDIA = frozenset({"image/jpeg", "image/png", "application/pdf"})


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


@dataclass
class ProbeRuntime:
    records: PostgresRecordKernel
    vault: LocalPrivateByteVault
    typed: TypedSchemaKernel
    content: BoundedContentValidationKernel
    schema: str
    vault_root: Path


def _pass(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "PASS", message)


def _fail(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "FAIL", message)


def _png_bytes(rgb: tuple[int, int, int]) -> bytes:
    from PIL import Image  # type: ignore

    buffer = BytesIO()
    Image.new("RGB", (12, 12), rgb).save(buffer, format="PNG")
    return buffer.getvalue()


def _payload(invoice_id: str, source_id: str, content: bytes) -> dict:
    digest = hashlib.sha256(content).hexdigest()
    return {
        "invoice_id": invoice_id,
        "files": (
            {
                "filename": f"{source_id}.png",
                "media_type": "image/png",
                "content": content,
                "expected_source_id": source_id,
                "expected_content_hash": digest,
            },
        ),
        "expected_sources": (
            {
                "content_kind": "invoice_source",
                "content_id": source_id,
                "content_hash": digest,
                "size_bytes": len(content),
                "media_type": "image/png",
            },
        ),
    }


def _authority(invoice_id: str) -> AuthorityKernel:
    return AuthorityKernel(
        principals=(PrincipalRecord("attach-agent", "agent"),),
        credentials=(
            CredentialRecord(
                "attach-credential",
                "attach-agent",
                LOCAL_AGENT_BOUNDARY,
                credential_digest(AGENT_SECRET),
            ),
        ),
        grants=(
            GrantRecord(
                "attach-grant",
                "attach-agent",
                "invoice.source.attach",
                InvoiceSourceAttachExecutor.resource_scope(invoice_id),
                effect_scope=EFFECTS,
                disclosure_scope=DISCLOSURES,
            ),
        ),
        policies=(
            CapabilityPolicy(
                "invoice.source.attach",
                effects=EFFECTS,
                disclosure_allow=DISCLOSURES,
            ),
        ),
    )


def _executor(runtime: ProbeRuntime, invoice_id: str, *, vault=None) -> InvoiceSourceAttachExecutor:
    return InvoiceSourceAttachExecutor(
        authority=_authority(invoice_id),
        typed_schema=runtime.typed,
        records=runtime.records,
        byte_vault=runtime.vault if vault is None else vault,
        content_validation=runtime.content,
    )


def _staging_count(vault: LocalPrivateByteVault) -> int:
    return sum(1 for path in vault.staging_root.iterdir() if path.is_file())


def _setup_runtime(environment: dict[str, str]) -> ProbeRuntime:
    config = ProtectedConfigurationKernel.from_environment(
        (
            ConfigurationBinding("database.primary", DB_ENV),
            ConfigurationBinding("source_vault.root", VAULT_ENV),
        ),
        environment,
    )
    config.require_ready()
    schema = f"spec_workbench_attach_{uuid.uuid4().hex[:12]}"
    vault_parent = Path(environment[VAULT_ENV]).expanduser().resolve()
    if not vault_parent.is_absolute():
        raise RuntimeError("configured vault parent must resolve to an absolute path")
    vault_parent.mkdir(parents=True, exist_ok=True)
    vault_root = vault_parent / f"runtime-{uuid.uuid4().hex[:12]}"

    records = config.use_for_host_provider(
        "database.primary", lambda dsn: PostgresRecordKernel(dsn, schema=schema)
    )
    records.initialize()
    vault = config.use_for_host_provider(
        "source_vault.root", lambda _root: LocalPrivateByteVault(vault_root)
    )
    return ProbeRuntime(
        records=records,
        vault=vault,
        typed=TypedSchemaKernel(),
        content=BoundedContentValidationKernel(
            max_size_bytes=MAX_BYTES,
            accepted_media_types=ACCEPTED_MEDIA,
        ),
        schema=schema,
        vault_root=vault_root,
    )


def _probe_authority_before_effect(runtime: ProbeRuntime) -> ProbeResult:
    allowed_invoice = f"inv-auth-{uuid.uuid4().hex[:8]}"
    denied_invoice = f"inv-denied-{uuid.uuid4().hex[:8]}"
    source_id = "source-1"
    content = _png_bytes((10, 20, 30))
    executor = _executor(runtime, allowed_invoice)
    before = _staging_count(runtime.vault)

    missing_target = _payload(denied_invoice, source_id, content)
    missing_target.pop("invoice_id")
    try:
        executor.execute(
            missing_target,
            credential_id="attach-credential",
            credential_material=AGENT_SECRET,
            interaction_id="attach-auth-missing-target",
        )
    except TypedSchemaValidationError:
        pass
    except Exception as exc:
        return _fail("ATTACH-PROBE-001", f"unexpected missing-target failure: {type(exc).__name__}: {exc}")
    else:
        return _fail("ATTACH-PROBE-001", "missing explicit invoice target reached execution")

    try:
        executor.execute(
            _payload(denied_invoice, source_id, content),
            credential_id="attach-credential",
            credential_material=AGENT_SECRET,
            interaction_id="attach-auth-wrong-scope",
        )
    except AuthorizationDenied:
        pass
    except Exception as exc:
        return _fail("ATTACH-PROBE-001", f"unexpected wrong-scope failure: {type(exc).__name__}: {exc}")
    else:
        return _fail("ATTACH-PROBE-001", "wrong invoice scope was authorized")

    if _staging_count(runtime.vault) != before:
        return _fail("ATTACH-PROBE-001", "unauthorized or untyped invocation created staged bytes")
    if runtime.records.read_record(INVOICE_NAMESPACE, denied_invoice) is not None:
        return _fail("ATTACH-PROBE-001", "unauthorized invocation created invoice metadata")
    if not any(event.event_type == "authority.refusal" for event in runtime.records.read_audit()):
        return _fail("ATTACH-PROBE-001", "authorization refusal was not persisted to durable audit")
    return _pass(
        "ATTACH-PROBE-001",
        "typed explicit target and exact invoice authority were required before byte or metadata effects",
    )


def _probe_binding_and_validation_before_stage(runtime: ProbeRuntime) -> ProbeResult:
    invoice_id = f"inv-bind-{uuid.uuid4().hex[:8]}"
    source_id = "source-bind"
    expected_content = _png_bytes((40, 50, 60))
    wrong_content = _png_bytes((70, 80, 90))
    expected_hash = hashlib.sha256(expected_content).hexdigest()
    seed_expected_missing_source(
        runtime.records,
        invoice_id=invoice_id,
        source_id=source_id,
        media_type="image/png",
        expected_hash=expected_hash,
    )
    executor = _executor(runtime, invoice_id)
    before = _staging_count(runtime.vault)

    try:
        executor.execute(
            _payload(invoice_id, source_id, wrong_content),
            credential_id="attach-credential",
            credential_material=AGENT_SECRET,
            interaction_id="attach-binding-mismatch",
        )
    except InvoiceSourceAttachRejected as exc:
        if exc.code != "durable_expected_content_hash_mismatch":
            return _fail("ATTACH-PROBE-002", f"unexpected binding rejection: {exc.code}")
    except Exception as exc:
        return _fail("ATTACH-PROBE-002", f"unexpected binding failure: {type(exc).__name__}: {exc}")
    else:
        return _fail("ATTACH-PROBE-002", "wrong content hash was accepted")

    malformed = b"not-a-real-png"
    try:
        executor.execute(
            _payload(invoice_id, source_id, malformed),
            credential_id="attach-credential",
            credential_material=AGENT_SECRET,
            interaction_id="attach-malformed-content",
        )
    except InvoiceSourceAttachRejected as exc:
        if exc.code != "content_validation_rejected":
            return _fail("ATTACH-PROBE-002", f"unexpected malformed rejection: {exc.code}")
    except Exception as exc:
        return _fail("ATTACH-PROBE-002", f"unexpected malformed failure: {type(exc).__name__}: {exc}")
    else:
        return _fail("ATTACH-PROBE-002", "malformed content was accepted")

    if _staging_count(runtime.vault) != before:
        return _fail("ATTACH-PROBE-002", "rejected source/hash/content validation left staged bytes")
    if runtime.records.read_record(
        PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
    ) is not None:
        return _fail("ATTACH-PROBE-002", "rejected validation created a publication journal")
    state = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
    if state is None or state.payload["source_states"][source_id]["status"] != "missing":
        return _fail("ATTACH-PROBE-002", "rejected validation changed source availability")
    return _pass(
        "ATTACH-PROBE-002",
        "expected source/hash and bounded parser validation failed closed before staging or metadata publication",
    )


def _execute_success(runtime: ProbeRuntime, invoice_id: str, source_id: str, content: bytes, *, expected_hash=None):
    digest = hashlib.sha256(content).hexdigest()
    seed_expected_missing_source(
        runtime.records,
        invoice_id=invoice_id,
        source_id=source_id,
        media_type="image/png",
        expected_hash=digest if expected_hash is None else expected_hash,
    )
    executor = _executor(runtime, invoice_id)
    result = executor.execute(
        _payload(invoice_id, source_id, content),
        credential_id="attach-credential",
        credential_material=AGENT_SECRET,
        interaction_id=f"attach-{invoice_id}",
    )
    return executor, result, digest


def _probe_success_visibility(runtime: ProbeRuntime) -> ProbeResult:
    invoice_id = f"inv-success-{uuid.uuid4().hex[:8]}"
    source_id = "source-success"
    content = _png_bytes((100, 110, 120))
    try:
        _, result, digest = _execute_success(runtime, invoice_id, source_id, content)
        invoice = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        if invoice is None or publication is None:
            return _fail("ATTACH-PROBE-003", "successful attachment did not persist metadata")
        state = invoice.payload["source_states"][source_id]
        if state["status"] != "available" or state["content_hash"] != digest:
            return _fail("ATTACH-PROBE-003", "source became visible with incorrect state")
        if publication.payload["state"] != "published":
            return _fail("ATTACH-PROBE-003", "source was available before publication journal reached published")
        if not runtime.vault.verify(
            publication.payload["final_reference"], digest, len(content)
        ):
            return _fail("ATTACH-PROBE-003", "published final bytes did not verify")
        if result.items[0].result != "attached" or result.source_status.complete is not True:
            return _fail("ATTACH-PROBE-003", "safe result did not report completed attachment")
    except Exception as exc:
        return _fail("ATTACH-PROBE-003", f"successful attachment failed: {type(exc).__name__}: {exc}")
    return _pass(
        "ATTACH-PROBE-003",
        "metadata committed, bytes published and reverified, then source became available with a safe completed result",
    )


def _probe_idempotent_replay(runtime: ProbeRuntime) -> ProbeResult:
    invoice_id = f"inv-replay-{uuid.uuid4().hex[:8]}"
    source_id = "source-replay"
    content = _png_bytes((130, 140, 150))
    try:
        executor, _, _ = _execute_success(runtime, invoice_id, source_id, content)
        before_invoice = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        before_publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        result = executor.execute(
            _payload(invoice_id, source_id, content),
            credential_id="attach-credential",
            credential_material=AGENT_SECRET,
            interaction_id="attach-replay-second",
        )
        after_invoice = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        after_publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        if result.items[0].result != "already_attached":
            return _fail("ATTACH-PROBE-004", "equivalent replay did not converge on existing result")
        if None in (before_invoice, before_publication, after_invoice, after_publication):
            return _fail("ATTACH-PROBE-004", "replay metadata unexpectedly disappeared")
        if before_invoice.version != after_invoice.version or before_publication.version != after_publication.version:
            return _fail("ATTACH-PROBE-004", "equivalent replay mutated logical source/publication metadata")
    except Exception as exc:
        return _fail("ATTACH-PROBE-004", f"replay probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "ATTACH-PROBE-004",
        "equivalent replay returned the existing logical attachment without a duplicate metadata transition",
    )


def _probe_conflicting_bytes(runtime: ProbeRuntime) -> ProbeResult:
    invoice_id = f"inv-conflict-{uuid.uuid4().hex[:8]}"
    source_id = "source-conflict"
    first = _png_bytes((160, 170, 180))
    second = _png_bytes((190, 200, 210))
    first_hash = hashlib.sha256(first).hexdigest()
    seed_expected_missing_source(
        runtime.records,
        invoice_id=invoice_id,
        source_id=source_id,
        media_type="image/png",
        expected_hash=None,
    )
    executor = _executor(runtime, invoice_id)
    try:
        executor.execute(
            _payload(invoice_id, source_id, first),
            credential_id="attach-credential",
            credential_material=AGENT_SECRET,
            interaction_id="attach-conflict-first",
        )
        try:
            executor.execute(
                _payload(invoice_id, source_id, second),
                credential_id="attach-credential",
                credential_material=AGENT_SECRET,
                interaction_id="attach-conflict-second",
            )
        except InvoiceSourceAttachRejected as exc:
            if exc.code != "source_content_conflict":
                return _fail("ATTACH-PROBE-005", f"unexpected conflict code: {exc.code}")
        else:
            return _fail("ATTACH-PROBE-005", "conflicting second content replaced accepted source")

        publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        invoice = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if publication is None or invoice is None:
            return _fail("ATTACH-PROBE-005", "accepted evidence disappeared after conflict")
        if publication.payload["content_hash"] != first_hash or publication.payload["state"] != "published":
            return _fail("ATTACH-PROBE-005", "conflict changed accepted publication evidence")
        if invoice.payload["source_states"][source_id]["content_hash"] != first_hash:
            return _fail("ATTACH-PROBE-005", "conflict changed accepted source state")
    except Exception as exc:
        return _fail("ATTACH-PROBE-005", f"conflict probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "ATTACH-PROBE-005",
        "different bytes for one exact expected source were rejected without replacing accepted publication or source evidence",
    )


class _FailOncePublishVault:
    def __init__(self, delegate: LocalPrivateByteVault):
        self.delegate = delegate
        self.failed = False

    def publish(self, *args, **kwargs):
        if not self.failed:
            self.failed = True
            raise OSError("intentional crash-after-metadata-commit probe")
        return self.delegate.publish(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.delegate, name)


def _probe_recovery(runtime: ProbeRuntime) -> ProbeResult:
    invoice_id = f"inv-recovery-{uuid.uuid4().hex[:8]}"
    source_id = "source-recovery"
    content = _png_bytes((220, 100, 40))
    digest = hashlib.sha256(content).hexdigest()
    seed_expected_missing_source(
        runtime.records,
        invoice_id=invoice_id,
        source_id=source_id,
        media_type="image/png",
        expected_hash=digest,
    )
    fault_vault = _FailOncePublishVault(runtime.vault)
    executor = _executor(runtime, invoice_id, vault=fault_vault)
    try:
        try:
            executor.execute(
                _payload(invoice_id, source_id, content),
                credential_id="attach-credential",
                credential_material=AGENT_SECRET,
                interaction_id="attach-recovery-crash",
            )
        except InvoiceSourceAttachExecutionError as exc:
            if str(exc) != "publication_pending_recovery":
                return _fail("ATTACH-PROBE-006", f"unexpected interrupted result: {exc}")
        else:
            return _fail("ATTACH-PROBE-006", "intentional post-commit publication failure did not interrupt")

        pending = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        invoice = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        if pending is None or invoice is None or pending.payload["state"] != "metadata_committed":
            return _fail("ATTACH-PROBE-006", "interruption did not preserve recoverable publication journal")
        source_state = invoice.payload["source_states"][source_id]
        if source_state["status"] != "missing" or source_state["filename"] != f"{source_id}.png":
            return _fail("ATTACH-PROBE-006", "pending state claimed availability or lost attachment provenance")

        recovery_executor = _executor(runtime, invoice_id)
        result = recovery_executor.recover_pending_publication(invoice_id=invoice_id, source_id=source_id)
        settled = runtime.records.read_record(INVOICE_NAMESPACE, invoice_id)
        publication = runtime.records.read_record(
            PUBLICATION_NAMESPACE, publication_resource_id(invoice_id, source_id)
        )
        if result.items[0].result != "recovered":
            return _fail("ATTACH-PROBE-006", "startup recovery did not report recovered result")
        if settled is None or publication is None:
            return _fail("ATTACH-PROBE-006", "recovery lost durable state")
        if settled.payload["source_states"][source_id]["status"] != "available":
            return _fail("ATTACH-PROBE-006", "recovery did not settle source availability")
        if publication.payload["state"] != "published":
            return _fail("ATTACH-PROBE-006", "recovery did not settle publication state")
    except Exception as exc:
        return _fail("ATTACH-PROBE-006", f"recovery probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "ATTACH-PROBE-006",
        "crash after metadata commit preserved pending provenance and startup recovery converged on one published verified source",
    )


def _probe_no_disclosure(runtime: ProbeRuntime) -> ProbeResult:
    invoice_id = f"inv-disclosure-{uuid.uuid4().hex[:8]}"
    source_id = "source-disclosure"
    content = _png_bytes((20, 180, 80))
    try:
        _, result, _ = _execute_success(runtime, invoice_id, source_id, content)
        output_text = repr(result)
        audit_text = repr(runtime.records.read_audit())
        forbidden = (
            AGENT_SECRET,
            str(runtime.vault.root),
            "staging:",
            "blob:",
            DB_ENV,
            VAULT_ENV,
        )
        if any(value in output_text for value in forbidden):
            return _fail("ATTACH-PROBE-007", "caller output disclosed a protected storage/config/credential value")
        if any(value in audit_text for value in forbidden):
            return _fail("ATTACH-PROBE-007", "durable audit disclosed a protected storage/config/credential value")
        if not any(event.event_type == "invoice.source.attach" for event in runtime.records.read_audit()):
            return _fail("ATTACH-PROBE-007", "protected effect produced no durable attach audit")
    except Exception as exc:
        return _fail("ATTACH-PROBE-007", f"disclosure/audit probe failed: {type(exc).__name__}: {exc}")
    return _pass(
        "ATTACH-PROBE-007",
        "safe output and durable append-only audit contained no raw storage references, config keys, or reusable credential material",
    )


def run_probe(environment: dict[str, str] | None = None) -> ProbeReport:
    env = dict(os.environ if environment is None else environment)
    probe_ids = tuple(f"ATTACH-PROBE-{index:03d}" for index in range(1, 8))
    try:
        runtime = _setup_runtime(env)
    except (ProtectedConfigurationNotReady, KeyError) as exc:
        return ProbeReport(
            PROBE_SCHEMA_VERSION,
            "invoice.source.attach/attach_expected_missing_source",
            "block",
            tuple(ProbeResult(probe_id, "UNVERIFIED", f"runtime configuration missing: {exc}") for probe_id in probe_ids),
        )
    except Exception as exc:
        return ProbeReport(
            PROBE_SCHEMA_VERSION,
            "invoice.source.attach/attach_expected_missing_source",
            "block",
            tuple(ProbeResult(probe_id, "UNVERIFIED", f"runtime setup failed: {type(exc).__name__}: {exc}") for probe_id in probe_ids),
        )

    results: list[ProbeResult] = []
    try:
        for probe in (
            _probe_authority_before_effect,
            _probe_binding_and_validation_before_stage,
            _probe_success_visibility,
            _probe_idempotent_replay,
            _probe_conflicting_bytes,
            _probe_recovery,
            _probe_no_disclosure,
        ):
            results.append(probe(runtime))
    finally:
        try:
            runtime.records.drop_probe_schema()
        except Exception as exc:
            results.append(_fail("PROBE-CLEANUP", f"database cleanup failed: {type(exc).__name__}: {exc}"))
        try:
            shutil.rmtree(runtime.vault_root)
        except FileNotFoundError:
            pass
        except Exception as exc:
            results.append(_fail("PROBE-CLEANUP", f"vault cleanup failed: {type(exc).__name__}: {exc}"))

    status = "pass" if len(results) == 7 and all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(
        PROBE_SCHEMA_VERSION,
        "invoice.source.attach/attach_expected_missing_source",
        status,
        tuple(results),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    report = run_probe()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
