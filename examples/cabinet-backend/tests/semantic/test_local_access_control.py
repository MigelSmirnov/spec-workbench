"""Local access control: refusals are typed, never a string prefix.

A revoked or rotated credential is an authentication failure (401), never a
missing capability (403); a live principal without the exact capability is
forbidden. Both decisions are recorded as secret-free audit evidence.
"""

import pytest


def test_enrolled_service_authenticates_and_is_authorized_for_its_capability(semantic_runtime):
    issued = semantic_runtime.enroll_local_service(display_name="scanner", capabilities=("attach_local_source",))

    context = semantic_runtime.authenticate(issued.credential)
    decision = semantic_runtime.authorize(context, "attach_local_source")

    assert decision.allowed is True
    assert context.principal_id == issued.principal_id
    assert "scanner" not in issued.principal_id and "scanner" not in issued.credential_id
    assert semantic_runtime.audit_results() == ["allowed", "allowed", "allowed"]


def test_missing_capability_is_forbidden_not_unauthenticated(semantic_runtime):
    issued = semantic_runtime.enroll_local_service(display_name="scanner", capabilities=("attach_local_source",))
    context = semantic_runtime.authenticate(issued.credential)

    with pytest.raises(semantic_runtime.OperationForbiddenError):
        semantic_runtime.authorize(context, "record_source_loss")

    assert semantic_runtime.last_audit().reason_code == "operation_forbidden"


def test_revoked_principal_is_unauthenticated_even_with_a_valid_looking_context(semantic_runtime):
    issued = semantic_runtime.enroll_local_service(display_name="scanner", capabilities=("attach_local_source",))
    context = semantic_runtime.authenticate(issued.credential)
    semantic_runtime.revoke_local_service_principal(issued.principal_id)

    with pytest.raises(semantic_runtime.AuthenticationRequiredError):
        semantic_runtime.authorize(context, "attach_local_source")
    with pytest.raises(semantic_runtime.AuthenticationRequiredError):
        semantic_runtime.authenticate(issued.credential)

    assert semantic_runtime.last_audit().reason_code in {"principal_revoked", "credential_revoked"}


def test_rotated_out_token_is_unauthenticated_and_new_token_works(semantic_runtime):
    issued = semantic_runtime.enroll_local_service(display_name="scanner", capabilities=("attach_local_source",))
    replacement = semantic_runtime.rotate_local_service_credential(issued.principal_id)

    with pytest.raises(semantic_runtime.AuthenticationRequiredError):
        semantic_runtime.authenticate(issued.credential)
    context = semantic_runtime.authenticate(replacement.credential)

    assert context.credential_id == replacement.credential_id
    assert semantic_runtime.authorize(context, "attach_local_source").allowed is True


def test_unknown_and_malformed_tokens_are_unauthenticated_without_secret_leak(semantic_runtime):
    for token in ("not-a-token", "crd-00000000000000000000000000000000.deadbeef"):
        with pytest.raises(semantic_runtime.AuthenticationRequiredError):
            semantic_runtime.authenticate(token)
    assert all(record.reason_code != "secret_mismatch" or record.credential_id is not None for record in semantic_runtime.audit_records())
    assert not any("deadbeef" in (record.evidence_id or "") for record in semantic_runtime.audit_records())
