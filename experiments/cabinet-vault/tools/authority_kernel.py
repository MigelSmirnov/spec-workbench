#!/usr/bin/env python3
"""Generic authority kernel for authenticated, scoped, policy-bound host invocations."""
from __future__ import annotations

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, FrozenSet, Mapping, TypeVar


T = TypeVar("T")


LOCAL_AGENT_BOUNDARY = "local_agent"
SYNCHRONIZATION_BOUNDARY = "synchronization"
_PROTECTED_CALLER_ASSERTIONS = frozenset(
    {
        "authenticated_principal",
        "authorization_decision",
        "grant_state",
        "actor_from_authenticated_principal",
        "delegated_by",
        "credential_material",
    }
)


class AuthorityError(RuntimeError):
    pass


class AuthenticationDenied(AuthorityError):
    pass


class AuthorizationDenied(AuthorityError):
    pass


@dataclass(frozen=True)
class PrincipalRecord:
    principal_id: str
    kind: str
    active: bool = True


@dataclass(frozen=True)
class CredentialRecord:
    credential_id: str
    principal_id: str
    credential_class: str
    verifier_digest: str
    active: bool = True


@dataclass(frozen=True)
class GrantRecord:
    grant_id: str
    principal_id: str
    capability: str
    resource_scope: str
    effect_scope: FrozenSet[str] = frozenset()
    disclosure_scope: FrozenSet[str] = frozenset()
    active: bool = True


@dataclass(frozen=True)
class CapabilityPolicy:
    capability: str
    effects: FrozenSet[str] = frozenset()
    disclosure_allow: FrozenSet[str] = frozenset()


@dataclass(frozen=True)
class ActorBinding:
    principal_id: str
    actor_kind: str
    interaction_id: str
    delegated_by: str | None = None


@dataclass(frozen=True)
class AuthorizationDecision:
    decision_id: str
    principal_id: str
    capability: str
    resource_scope: str
    actor: ActorBinding
    effects: FrozenSet[str]
    disclosures: FrozenSet[str]


@dataclass(frozen=True)
class AuditEvidence:
    evidence_id: str
    principal_id_or_unknown: str
    capability_or_operation: str
    resource_scope_or_target: str
    result: str
    reason_code: str
    occurred_at: str
    declared_effects: tuple[str, ...] = ()


def credential_digest(secret: str) -> str:
    if not isinstance(secret, str) or not secret:
        raise AuthorityError("credential material must be a non-empty string")
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


class AuthorityKernel:
    """Candidate generic host authority provider; no Cabinet role vocabulary."""

    def __init__(
        self,
        principals: tuple[PrincipalRecord, ...],
        credentials: tuple[CredentialRecord, ...],
        grants: tuple[GrantRecord, ...],
        policies: tuple[CapabilityPolicy, ...],
    ) -> None:
        self._principals = {item.principal_id: item for item in principals}
        self._credentials = {item.credential_id: item for item in credentials}
        self._grants = {item.grant_id: item for item in grants}
        self._policies = {item.capability: item for item in policies}
        if len(self._principals) != len(principals):
            raise AuthorityError("principal ids must be unique")
        if len(self._credentials) != len(credentials):
            raise AuthorityError("credential ids must be unique")
        if len(self._grants) != len(grants):
            raise AuthorityError("grant ids must be unique")
        if len(self._policies) != len(policies):
            raise AuthorityError("capability policies must be unique")
        self._audit: list[AuditEvidence] = []

    @property
    def audit_evidence(self) -> tuple[AuditEvidence, ...]:
        return tuple(self._audit)

    def _audit_event(
        self,
        *,
        principal_id: str | None,
        capability: str,
        resource_scope: str,
        result: str,
        reason_code: str,
        effects: FrozenSet[str] = frozenset(),
    ) -> None:
        self._audit.append(
            AuditEvidence(
                evidence_id=uuid.uuid4().hex,
                principal_id_or_unknown=principal_id or "unknown",
                capability_or_operation=capability,
                resource_scope_or_target=resource_scope,
                result=result,
                reason_code=reason_code,
                occurred_at=datetime.now(timezone.utc).isoformat(),
                declared_effects=tuple(sorted(effects)),
            )
        )

    @staticmethod
    def _reject_protected_caller_assertions(caller_assertions: Mapping[str, object] | None) -> None:
        if not caller_assertions:
            return
        protected = set(caller_assertions) & _PROTECTED_CALLER_ASSERTIONS
        if protected:
            raise AuthorizationDenied(
                "caller cannot supply protected host authority fields: "
                + ", ".join(sorted(protected))
            )

    def revoke_principal(self, principal_id: str) -> None:
        principal = self._principals.get(principal_id)
        if principal is None:
            raise AuthorityError("unknown principal")
        self._principals[principal_id] = PrincipalRecord(principal.principal_id, principal.kind, False)

    def revoke_credential(self, credential_id: str) -> None:
        credential = self._credentials.get(credential_id)
        if credential is None:
            raise AuthorityError("unknown credential")
        self._credentials[credential_id] = CredentialRecord(
            credential.credential_id,
            credential.principal_id,
            credential.credential_class,
            credential.verifier_digest,
            False,
        )

    def authenticate(
        self,
        credential_id: str,
        credential_material: str,
        *,
        required_boundary: str,
    ) -> PrincipalRecord:
        credential = self._credentials.get(credential_id)
        if credential is None or not credential.active:
            self._audit_event(
                principal_id=None if credential is None else credential.principal_id,
                capability="authenticate",
                resource_scope=required_boundary,
                result="deny",
                reason_code="credential_inactive_or_unknown",
            )
            raise AuthenticationDenied("credential is inactive or unknown")

        if credential.credential_class != required_boundary:
            self._audit_event(
                principal_id=credential.principal_id,
                capability="authenticate",
                resource_scope=required_boundary,
                result="deny",
                reason_code="credential_trust_boundary_mismatch",
            )
            raise AuthenticationDenied("credential class does not match trust boundary")

        presented = credential_digest(credential_material)
        if not hmac.compare_digest(presented, credential.verifier_digest):
            self._audit_event(
                principal_id=credential.principal_id,
                capability="authenticate",
                resource_scope=required_boundary,
                result="deny",
                reason_code="credential_verification_failed",
            )
            raise AuthenticationDenied("credential verification failed")

        principal = self._principals.get(credential.principal_id)
        if principal is None or not principal.active:
            self._audit_event(
                principal_id=credential.principal_id,
                capability="authenticate",
                resource_scope=required_boundary,
                result="deny",
                reason_code="principal_inactive_or_unknown",
            )
            raise AuthenticationDenied("principal is inactive or unknown")
        return principal

    def authorize(
        self,
        principal: PrincipalRecord,
        *,
        capability: str,
        resource_scope: str,
        requested_effects: FrozenSet[str] = frozenset(),
        requested_disclosures: FrozenSet[str] = frozenset(),
        interaction_id: str,
        caller_assertions: Mapping[str, object] | None = None,
    ) -> AuthorizationDecision:
        try:
            self._reject_protected_caller_assertions(caller_assertions)
        except AuthorizationDenied:
            self._audit_event(
                principal_id=principal.principal_id,
                capability=capability,
                resource_scope=resource_scope,
                result="deny",
                reason_code="caller_supplied_protected_authority",
            )
            raise

        current_principal = self._principals.get(principal.principal_id)
        if current_principal is None or not current_principal.active:
            self._audit_event(
                principal_id=principal.principal_id,
                capability=capability,
                resource_scope=resource_scope,
                result="deny",
                reason_code="principal_revoked",
            )
            raise AuthorizationDenied("principal is not currently active")

        policy = self._policies.get(capability)
        if policy is None:
            self._audit_event(
                principal_id=principal.principal_id,
                capability=capability,
                resource_scope=resource_scope,
                result="deny",
                reason_code="capability_policy_missing",
            )
            raise AuthorizationDenied("capability has no declared host policy")

        grant = next(
            (
                item
                for item in self._grants.values()
                if item.active
                and item.principal_id == principal.principal_id
                and item.capability == capability
                and item.resource_scope == resource_scope
            ),
            None,
        )
        if grant is None:
            self._audit_event(
                principal_id=principal.principal_id,
                capability=capability,
                resource_scope=resource_scope,
                result="deny",
                reason_code="exact_grant_or_resource_scope_missing",
            )
            raise AuthorizationDenied("exact capability and resource scope grant required")

        if not requested_effects.issubset(policy.effects) or not requested_effects.issubset(
            grant.effect_scope
        ):
            self._audit_event(
                principal_id=principal.principal_id,
                capability=capability,
                resource_scope=resource_scope,
                result="deny",
                reason_code="effect_not_authorized",
                effects=requested_effects,
            )
            raise AuthorizationDenied("requested effect is not explicitly authorized")

        if not requested_disclosures.issubset(policy.disclosure_allow) or not requested_disclosures.issubset(
            grant.disclosure_scope
        ):
            self._audit_event(
                principal_id=principal.principal_id,
                capability=capability,
                resource_scope=resource_scope,
                result="deny",
                reason_code="disclosure_not_authorized",
                effects=requested_effects,
            )
            raise AuthorizationDenied("requested disclosure is not explicitly authorized")

        actor = ActorBinding(
            principal_id=current_principal.principal_id,
            actor_kind=current_principal.kind,
            interaction_id=interaction_id,
            delegated_by=None,
        )
        decision = AuthorizationDecision(
            decision_id=uuid.uuid4().hex,
            principal_id=current_principal.principal_id,
            capability=capability,
            resource_scope=resource_scope,
            actor=actor,
            effects=requested_effects,
            disclosures=requested_disclosures,
        )
        self._audit_event(
            principal_id=current_principal.principal_id,
            capability=capability,
            resource_scope=resource_scope,
            result="allow",
            reason_code="exact_grant_authorized",
            effects=requested_effects,
        )
        return decision

    def invoke(
        self,
        *,
        credential_id: str,
        credential_material: str,
        required_boundary: str,
        capability: str,
        resource_scope: str,
        interaction_id: str,
        operation: Callable[[AuthorizationDecision], T],
        requested_effects: FrozenSet[str] = frozenset(),
        requested_disclosures: FrozenSet[str] = frozenset(),
        caller_assertions: Mapping[str, object] | None = None,
    ) -> T:
        principal = self.authenticate(
            credential_id,
            credential_material,
            required_boundary=required_boundary,
        )
        decision = self.authorize(
            principal,
            capability=capability,
            resource_scope=resource_scope,
            requested_effects=requested_effects,
            requested_disclosures=requested_disclosures,
            interaction_id=interaction_id,
            caller_assertions=caller_assertions,
        )
        return operation(decision)
