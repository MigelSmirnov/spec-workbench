#!/usr/bin/env python3
"""Execute AUTH-PROBE-001..008 against the generic authority kernel candidate."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass

from authority_kernel import (
    LOCAL_AGENT_BOUNDARY,
    SYNCHRONIZATION_BOUNDARY,
    AuthenticationDenied,
    AuthorityKernel,
    AuthorizationDenied,
    CapabilityPolicy,
    CredentialRecord,
    GrantRecord,
    PrincipalRecord,
    credential_digest,
)


PROBE_SCHEMA_VERSION = "spec_workbench_authority_kernel_probe.v0"
AGENT_SECRET = "probe-agent-secret-91e8f3"
SYNC_SECRET = "probe-sync-secret-70d1c4"
CAPABILITY = "example.source.attach"
RESOURCE = "example-resource:invoice-1"
EFFECTS = frozenset({"source_byte_write", "record_write"})
DISCLOSURES = frozenset({"safe_result", "content_digest"})


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


def _kernel() -> AuthorityKernel:
    return AuthorityKernel(
        principals=(
            PrincipalRecord("agent-principal", "agent"),
            PrincipalRecord("sync-principal", "synchronization_node"),
        ),
        credentials=(
            CredentialRecord(
                "agent-credential",
                "agent-principal",
                LOCAL_AGENT_BOUNDARY,
                credential_digest(AGENT_SECRET),
            ),
            CredentialRecord(
                "sync-credential",
                "sync-principal",
                SYNCHRONIZATION_BOUNDARY,
                credential_digest(SYNC_SECRET),
            ),
        ),
        grants=(
            GrantRecord(
                "agent-grant",
                "agent-principal",
                CAPABILITY,
                RESOURCE,
                effect_scope=EFFECTS,
                disclosure_scope=DISCLOSURES,
            ),
        ),
        policies=(
            CapabilityPolicy(
                CAPABILITY,
                effects=EFFECTS,
                disclosure_allow=DISCLOSURES,
            ),
        ),
    )


def _pass(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "PASS", message)


def _fail(probe_id: str, message: str) -> ProbeResult:
    return ProbeResult(probe_id, "FAIL", message)


def _probe_caller_decision_cannot_authorize() -> ProbeResult:
    kernel = _kernel()
    called = False

    def operation(_decision):
        nonlocal called
        called = True
        return "mutated"

    try:
        kernel.invoke(
            credential_id="agent-credential",
            credential_material=AGENT_SECRET,
            required_boundary=LOCAL_AGENT_BOUNDARY,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction-001",
            requested_effects=frozenset({"record_write"}),
            operation=operation,
            caller_assertions={"authorization_decision": "forged-allow"},
        )
    except AuthorizationDenied:
        if called:
            return _fail("AUTH-PROBE-001", "operation executed despite forged caller authority")
        return _pass(
            "AUTH-PROBE-001",
            "caller-supplied authorization_decision was rejected before protected operation execution",
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-001", f"unexpected failure: {type(exc).__name__}: {exc}")
    return _fail("AUTH-PROBE-001", "forged caller authorization was accepted")


def _probe_revocation_blocks_future_authority() -> ProbeResult:
    credential_kernel = _kernel()
    credential_kernel.revoke_credential("agent-credential")
    try:
        credential_kernel.authenticate(
            "agent-credential", AGENT_SECRET, required_boundary=LOCAL_AGENT_BOUNDARY
        )
    except AuthenticationDenied:
        pass
    else:
        return _fail("AUTH-PROBE-002", "revoked credential authenticated")

    principal_kernel = _kernel()
    principal_kernel.revoke_principal("agent-principal")
    try:
        principal_kernel.authenticate(
            "agent-credential", AGENT_SECRET, required_boundary=LOCAL_AGENT_BOUNDARY
        )
    except AuthenticationDenied:
        return _pass(
            "AUTH-PROBE-002",
            "revoked credential and revoked principal both lost future authentication authority",
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-002", f"unexpected failure: {type(exc).__name__}: {exc}")
    return _fail("AUTH-PROBE-002", "revoked principal authenticated")


def _probe_exact_resource_scope() -> ProbeResult:
    kernel = _kernel()
    principal = kernel.authenticate(
        "agent-credential", AGENT_SECRET, required_boundary=LOCAL_AGENT_BOUNDARY
    )
    try:
        kernel.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope="example-resource:invoice-2",
            interaction_id="interaction-003",
        )
    except AuthorizationDenied:
        return _pass(
            "AUTH-PROBE-003",
            "grant for one exact resource scope could not authorize a different target",
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-003", f"unexpected failure: {type(exc).__name__}: {exc}")
    return _fail("AUTH-PROBE-003", "authorization succeeded without exact resource scope")


def _probe_sync_rejected_at_local_agent_boundary() -> ProbeResult:
    kernel = _kernel()
    try:
        kernel.authenticate(
            "sync-credential", SYNC_SECRET, required_boundary=LOCAL_AGENT_BOUNDARY
        )
    except AuthenticationDenied:
        return _pass(
            "AUTH-PROBE-004",
            "synchronization credential was rejected at the local-agent trust boundary",
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-004", f"unexpected failure: {type(exc).__name__}: {exc}")
    return _fail("AUTH-PROBE-004", "synchronization credential crossed into local-agent authority")


def _probe_local_agent_rejected_at_sync_boundary() -> ProbeResult:
    kernel = _kernel()
    try:
        kernel.authenticate(
            "agent-credential", AGENT_SECRET, required_boundary=SYNCHRONIZATION_BOUNDARY
        )
    except AuthenticationDenied:
        return _pass(
            "AUTH-PROBE-005",
            "local-agent credential was rejected as synchronization authority",
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-005", f"unexpected failure: {type(exc).__name__}: {exc}")
    return _fail("AUTH-PROBE-005", "local-agent credential crossed into synchronization authority")


def _probe_effect_and_disclosure_default_deny() -> ProbeResult:
    kernel = _kernel()
    principal = kernel.authenticate(
        "agent-credential", AGENT_SECRET, required_boundary=LOCAL_AGENT_BOUNDARY
    )
    try:
        kernel.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction-006-effect",
            requested_effects=frozenset({"undeclared_effect"}),
        )
    except AuthorizationDenied:
        pass
    else:
        return _fail("AUTH-PROBE-006", "undeclared effect was authorized")

    try:
        kernel.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction-006-disclosure",
            requested_disclosures=frozenset({"raw_secret"}),
        )
    except AuthorizationDenied:
        return _pass(
            "AUTH-PROBE-006",
            "effect and disclosure requests outside explicit policy/grant bounds were denied",
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-006", f"unexpected failure: {type(exc).__name__}: {exc}")
    return _fail("AUTH-PROBE-006", "undeclared disclosure was authorized")


def _probe_actor_bound_from_authenticated_principal() -> ProbeResult:
    kernel = _kernel()
    observed = []

    def operation(decision):
        observed.append(decision)
        return "effect-complete"

    try:
        result = kernel.invoke(
            credential_id="agent-credential",
            credential_material=AGENT_SECRET,
            required_boundary=LOCAL_AGENT_BOUNDARY,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction-007",
            requested_effects=frozenset({"record_write"}),
            requested_disclosures=frozenset({"safe_result"}),
            operation=operation,
        )
    except Exception as exc:
        return _fail("AUTH-PROBE-007", f"unexpected failure: {type(exc).__name__}: {exc}")

    if result != "effect-complete" or len(observed) != 1:
        return _fail("AUTH-PROBE-007", "protected mutation did not receive exactly one host decision")
    decision = observed[0]
    if decision.principal_id != "agent-principal":
        return _fail("AUTH-PROBE-007", "decision principal did not come from authenticated evidence")
    if decision.actor.principal_id != "agent-principal" or decision.actor.actor_kind != "agent":
        return _fail("AUTH-PROBE-007", "actor was not bound from the authenticated principal")
    if decision.actor.interaction_id != "interaction-007" or decision.actor.delegated_by is not None:
        return _fail("AUTH-PROBE-007", "host actor provenance was not bound as declared")
    return _pass(
        "AUTH-PROBE-007",
        "protected mutation received actor provenance bound from the authenticated principal and host interaction",
    )


def _probe_audit_contains_no_reusable_secret() -> ProbeResult:
    kernel = _kernel()
    try:
        kernel.invoke(
            credential_id="agent-credential",
            credential_material=AGENT_SECRET,
            required_boundary=LOCAL_AGENT_BOUNDARY,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction-008",
            requested_effects=frozenset({"record_write"}),
            operation=lambda decision: decision.decision_id,
        )
        try:
            kernel.authenticate(
                "sync-credential", SYNC_SECRET, required_boundary=LOCAL_AGENT_BOUNDARY
            )
        except AuthenticationDenied:
            pass
    except Exception as exc:
        return _fail("AUTH-PROBE-008", f"unexpected failure: {type(exc).__name__}: {exc}")

    audit_text = repr(kernel.audit_evidence)
    secret_values = (AGENT_SECRET, SYNC_SECRET)
    if any(secret in audit_text for secret in secret_values):
        return _fail("AUTH-PROBE-008", "reusable credential material appeared in audit evidence")
    if not kernel.audit_evidence:
        return _fail("AUTH-PROBE-008", "authority decisions produced no audit evidence")
    return _pass(
        "AUTH-PROBE-008",
        "authentication/authorization audit evidence contained no reusable credential material",
    )


def run_probe() -> ProbeReport:
    probes = (
        _probe_caller_decision_cannot_authorize,
        _probe_revocation_blocks_future_authority,
        _probe_exact_resource_scope,
        _probe_sync_rejected_at_local_agent_boundary,
        _probe_local_agent_rejected_at_sync_boundary,
        _probe_effect_and_disclosure_default_deny,
        _probe_actor_bound_from_authenticated_principal,
        _probe_audit_contains_no_reusable_secret,
    )
    results = tuple(probe() for probe in probes)
    status = "pass" if all(item.status == "PASS" for item in results) else "block"
    return ProbeReport(PROBE_SCHEMA_VERSION, "authority_kernel", status, results)


def main() -> int:
    report = run_probe()
    print(json.dumps(asdict(report), indent=2, sort_keys=True))
    return 0 if report.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
