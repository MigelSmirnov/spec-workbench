from __future__ import annotations

import pytest

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
from authority_kernel_probe import run_probe


SECRET = "unit-agent-secret"
CAPABILITY = "example.read"
RESOURCE = "resource:one"


def kernel() -> AuthorityKernel:
    return AuthorityKernel(
        principals=(
            PrincipalRecord("agent-1", "agent"),
            PrincipalRecord("sync-1", "synchronization_node"),
        ),
        credentials=(
            CredentialRecord(
                "agent-cred",
                "agent-1",
                LOCAL_AGENT_BOUNDARY,
                credential_digest(SECRET),
            ),
            CredentialRecord(
                "sync-cred",
                "sync-1",
                SYNCHRONIZATION_BOUNDARY,
                credential_digest("sync-secret"),
            ),
        ),
        grants=(
            GrantRecord(
                "grant-1",
                "agent-1",
                CAPABILITY,
                RESOURCE,
                effect_scope=frozenset({"record_write"}),
                disclosure_scope=frozenset({"safe_result"}),
            ),
        ),
        policies=(
            CapabilityPolicy(
                CAPABILITY,
                effects=frozenset({"record_write"}),
                disclosure_allow=frozenset({"safe_result"}),
            ),
        ),
    )


def test_caller_cannot_supply_authorization_decision_or_delegation():
    subject = kernel()
    principal = subject.authenticate("agent-cred", SECRET, required_boundary=LOCAL_AGENT_BOUNDARY)

    with pytest.raises(AuthorizationDenied, match="protected host authority"):
        subject.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction",
            caller_assertions={"authorization_decision": "forged"},
        )

    with pytest.raises(AuthorizationDenied, match="protected host authority"):
        subject.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction",
            caller_assertions={"delegated_by": "self-asserted"},
        )


def test_exact_resource_scope_and_explicit_effect_disclosure_are_required():
    subject = kernel()
    principal = subject.authenticate("agent-cred", SECRET, required_boundary=LOCAL_AGENT_BOUNDARY)

    with pytest.raises(AuthorizationDenied, match="exact capability and resource scope"):
        subject.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope="resource:two",
            interaction_id="interaction",
        )

    with pytest.raises(AuthorizationDenied, match="effect"):
        subject.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction",
            requested_effects=frozenset({"undeclared"}),
        )

    with pytest.raises(AuthorizationDenied, match="disclosure"):
        subject.authorize(
            principal,
            capability=CAPABILITY,
            resource_scope=RESOURCE,
            interaction_id="interaction",
            requested_disclosures=frozenset({"raw_secret"}),
        )


def test_credential_classes_do_not_cross_trust_boundaries():
    subject = kernel()

    with pytest.raises(AuthenticationDenied):
        subject.authenticate(
            "sync-cred", "sync-secret", required_boundary=LOCAL_AGENT_BOUNDARY
        )
    with pytest.raises(AuthenticationDenied):
        subject.authenticate(
            "agent-cred", SECRET, required_boundary=SYNCHRONIZATION_BOUNDARY
        )


def test_actor_is_bound_from_authenticated_principal_and_audit_omits_secret():
    subject = kernel()
    observed = []

    result = subject.invoke(
        credential_id="agent-cred",
        credential_material=SECRET,
        required_boundary=LOCAL_AGENT_BOUNDARY,
        capability=CAPABILITY,
        resource_scope=RESOURCE,
        interaction_id="interaction-7",
        requested_effects=frozenset({"record_write"}),
        requested_disclosures=frozenset({"safe_result"}),
        operation=lambda decision: observed.append(decision) or "ok",
    )

    assert result == "ok"
    assert observed[0].actor.principal_id == "agent-1"
    assert observed[0].actor.actor_kind == "agent"
    assert observed[0].actor.interaction_id == "interaction-7"
    assert SECRET not in repr(subject.audit_evidence)


def test_full_authority_probe_passes():
    report = run_probe()

    assert report.status == "pass"
    assert [item.probe_id for item in report.results] == [
        "AUTH-PROBE-001",
        "AUTH-PROBE-002",
        "AUTH-PROBE-003",
        "AUTH-PROBE-004",
        "AUTH-PROBE-005",
        "AUTH-PROBE-006",
        "AUTH-PROBE-007",
        "AUTH-PROBE-008",
    ]
    assert {item.status for item in report.results} == {"PASS"}
