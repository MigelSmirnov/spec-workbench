"""Runtime acceptance oracle for Stage 7.1 Flow 3.

The Factory project supplies the ``semantic_runtime`` pytest fixture. The fixture
binds these implementation-independent scenarios to generated public operations
without changing the assertions below.
"""

import pytest


def test_refresh_preserves_cabinet_owned_state_and_never_writes_registry(semantic_runtime):
    state = semantic_runtime.registry_state(
        existing_project={
            "project_id": "P1",
            "display_name": "Old name",
            "address": "Old address",
            "status": "active",
            "cabinet_fields": {"local_note": "keep", "attention": "active"},
        }
    )
    observation = semantic_runtime.registry_observation(
        projects=[
            {
                "project_id": "P1",
                "display_name": "New name",
                "address": "New address",
                "status": "active",
            }
        ]
    )

    result = semantic_runtime.refresh_registry_context(state, observation)
    project = result.work_object("P1")

    assert project.registry_fields["display_name"] == "New name"
    assert project.registry_fields["address"] == "New address"
    assert project.cabinet_fields["local_note"] == "keep"
    assert semantic_runtime.registry_write_count() == 0


def test_absence_from_later_registry_observation_does_not_delete_or_complete_work_object(semantic_runtime):
    state = semantic_runtime.registry_state(
        existing_project={
            "project_id": "P1",
            "display_name": "Known project",
            "address": "A",
            "status": "active",
            "cabinet_fields": {"attention": "active"},
        }
    )
    observation = semantic_runtime.registry_observation(projects=[])

    result = semantic_runtime.refresh_registry_context(state, observation)

    assert result.has_work_object("P1")
    preserved = result.work_object("P1")
    assert preserved.was_deleted is False
    assert preserved.inferred_completed is False


def test_validation_classifies_active_match_but_never_rewrites_immutable_card_assignment(semantic_runtime):
    card = semantic_runtime.immutable_card_revision(
        invoice_id="INV-1", content_hash="card-hash", project_id="P1"
    )
    semantic_runtime.set_registry_observation(
        projects=[
            {
                "project_id": "P1",
                "display_name": "Project",
                "address": "A",
                "status": "active",
            }
        ]
    )
    before = semantic_runtime.card_assignment_snapshot(card)

    active_validation = semantic_runtime.validate_card_assignment(card)

    assert active_validation.result == "valid"
    assert semantic_runtime.card_assignment_snapshot(card) == before

    semantic_runtime.set_registry_observation(
        projects=[
            {
                "project_id": "P1",
                "display_name": "Project",
                "address": "A",
                "status": "archived",
            }
        ]
    )
    archived_validation = semantic_runtime.validate_card_assignment(card)

    assert archived_validation.result != "valid"
    assert archived_validation.requires_review is True
    assert archived_validation.inferred_completed is False
    assert semantic_runtime.card_assignment_snapshot(card) == before


def test_missing_recorded_validation_is_not_synthesized_from_current_registry(semantic_runtime):
    card = semantic_runtime.immutable_card_revision(
        invoice_id="INV-1", content_hash="card-hash", project_id="P1"
    )
    semantic_runtime.set_registry_observation(
        projects=[
            {
                "project_id": "P1",
                "display_name": "Project",
                "address": "A",
                "status": "active",
            }
        ]
    )
    semantic_runtime.clear_assignment_validation(card)

    with pytest.raises(semantic_runtime.AssignmentValidationNotFoundError):
        semantic_runtime.get_assignment_validation(card)
