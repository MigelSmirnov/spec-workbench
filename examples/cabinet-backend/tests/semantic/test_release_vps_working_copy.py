"""Runtime acceptance oracle for Stage 7.1 Flow 6.

The Factory project supplies the ``semantic_runtime`` pytest fixture. The fixture
binds these implementation-independent scenarios to generated public operations
without changing the assertions below.
"""

import pytest


def test_release_requires_complete_durable_local_coverage_for_exact_working_set(semantic_runtime):
    working_set = semantic_runtime.vps_working_set(
        project_id="P1",
        working_set_id="WS-1",
        required_obligations=["INV-A:SRC-1", "INV-B:SRC-2"],
    )
    semantic_runtime.set_durable_verification("INV-A:SRC-1", accepted=True)
    semantic_runtime.set_durable_verification("INV-B:SRC-2", accepted=False)
    semantic_runtime.set_sync_observation(working_set, consistent=True)

    with pytest.raises(semantic_runtime.VpsReleaseBlockedError):
        semantic_runtime.evaluate_vps_release(working_set)

    assert semantic_runtime.release_decision_count(working_set) == 0
    assert semantic_runtime.physical_release_count(working_set) == 0


def test_registry_status_or_sync_success_never_substitutes_for_missing_durable_proof(semantic_runtime):
    working_set = semantic_runtime.vps_working_set(
        project_id="P1",
        working_set_id="WS-1",
        required_obligations=["INV-A:SRC-1"],
    )
    semantic_runtime.set_registry_status("P1", "archived")
    semantic_runtime.set_sync_observation(working_set, consistent=True, status="delivered")
    semantic_runtime.clear_durable_verification("INV-A:SRC-1")

    with pytest.raises(semantic_runtime.VpsReleaseBlockedError):
        semantic_runtime.evaluate_vps_release(working_set)

    assert semantic_runtime.physical_release_count(working_set) == 0


def test_allowed_evaluation_is_policy_only_and_covers_every_required_obligation(semantic_runtime):
    working_set = semantic_runtime.vps_working_set(
        project_id="P1",
        working_set_id="WS-1",
        required_obligations=["INV-A:SRC-1", "INV-B:SRC-2"],
    )
    semantic_runtime.set_durable_verification("INV-A:SRC-1", accepted=True)
    semantic_runtime.set_durable_verification("INV-B:SRC-2", accepted=True)
    semantic_runtime.set_sync_observation(working_set, consistent=True)

    evaluation = semantic_runtime.evaluate_vps_release(working_set)

    assert evaluation.allowed is True
    assert set(evaluation.covered_obligations) == {"INV-A:SRC-1", "INV-B:SRC-2"}
    assert evaluation.working_set_id == "WS-1"
    assert semantic_runtime.physical_release_count(working_set) == 0


def test_stale_or_changed_working_set_cannot_be_authorized_from_old_evaluation(semantic_runtime):
    working_set = semantic_runtime.vps_working_set(
        project_id="P1",
        working_set_id="WS-1",
        required_obligations=["INV-A:SRC-1"],
    )
    semantic_runtime.set_durable_verification("INV-A:SRC-1", accepted=True)
    semantic_runtime.set_sync_observation(working_set, consistent=True)
    evaluation = semantic_runtime.evaluate_vps_release(working_set)

    semantic_runtime.add_working_set_obligation(working_set, "INV-B:SRC-2")

    with pytest.raises(semantic_runtime.VpsReleaseBlockedError):
        semantic_runtime.request_manual_vps_release(working_set, evaluation)

    assert semantic_runtime.release_decision_count(working_set) == 0
    assert semantic_runtime.physical_release_count(working_set) == 0


def test_repeated_equivalent_manual_release_decision_is_idempotent(semantic_runtime):
    working_set = semantic_runtime.vps_working_set(
        project_id="P1",
        working_set_id="WS-1",
        required_obligations=["INV-A:SRC-1"],
    )
    semantic_runtime.set_durable_verification("INV-A:SRC-1", accepted=True)
    semantic_runtime.set_sync_observation(working_set, consistent=True)
    evaluation = semantic_runtime.evaluate_vps_release(working_set)

    first = semantic_runtime.request_manual_vps_release(working_set, evaluation)
    second = semantic_runtime.request_manual_vps_release(working_set, evaluation)

    assert second.decision_id == first.decision_id
    assert semantic_runtime.release_decision_count(working_set) == 1
    assert semantic_runtime.physical_release_count(working_set) == 0
